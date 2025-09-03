import psycopg2
from psycopg2 import sql
from sklearn.model_selection import train_test_split
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import pickle
import os
import json


class DataPrep:
    def __init__(self, table_name, host, port, dbname, user, password, logger):

        self.table_name = table_name
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password

        self.logger = logger

        self.columns = [
            "query",
            "doc_title",
            "user_persona",
            "user_expertise",
            "created_at",
            "user_id",
            "relevance_score",
        ]
        self.alias = [
            "query",
            "doc",
            "user_persona",
            "user_expertise",
            "created_at",
            "user_id",
            "score",
        ]

        if len(self.alias) != len(self.columns):
            raise Exception("Length has to match between columns and alias")

        self.query = ",".join(
            [
                " ".join((list(tup)))
                for tup in zip(self.columns, ["as"] * len(self.columns), self.alias)
            ]
        )

        self.logger.info(
            f"Query: {self.query}, Columns: {self.columns}, Aliases: {self.alias}"
        )

    def fetch_psql_data(self):

        try:
            conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.dbname,
                user=self.user,
                password=self.password,
            )

            cursor = conn.cursor()

            # Use SQL composition to prevent SQL injection
            query = sql.SQL(f"SELECT {self.query}" f" FROM {self.table_name}").format(
                sql.Identifier(self.table_name)
            )
            cursor.execute(query)
            rows = cursor.fetchall()

            cursor.close()
            conn.close()

            self.logger.info(f"Fetched {len(rows)} rows from {self.table_name}")
            return rows

        except Exception as e:
            self.logger.error(f"Error: {e}")
            return []

    def save_metadata(self, train_df, feature_cols, artifacts_dir="artifacts"):
        """Save metadata including category mappings"""

        metadata = {
            "feature_columns": feature_cols,
            "persona_categories": train_df["user_persona"]
            .astype("category")
            .cat.categories.tolist(),
            "expertise_categories": train_df["user_expertise"]
            .astype("category")
            .cat.categories.tolist(),
            "timestamp": pd.Timestamp.now().isoformat(),
        }

        metadata_path = os.path.join(artifacts_dir, "metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        self.logger.info(f"Metadata saved to {metadata_path}")

    def psql_to_df(self, rows):
        df = pd.DataFrame(rows, columns=self.alias)
        return df

    @staticmethod
    def save_tfidf_vectorizer(vectorizer, filepath):
        with open(filepath, "wb") as f:
            pickle.dump(vectorizer, f)

    @staticmethod
    def jaccard_similarity(q, d):
        q_words = set(re.findall(r"\w+", q.lower()))
        d_words = set(re.findall(r"\w+", d.lower()))
        if not q_words and not d_words:
            return 0.0
        return len(q_words & d_words) / len(q_words | d_words)

    @staticmethod
    def split_query_user(df, test_size=0.2, random_state=42):
        pairs = df[["query", "user_id"]].drop_duplicates()
        train_pairs, test_pairs = train_test_split(
            pairs, test_size=test_size, random_state=random_state
        )
        train_df = df.merge(train_pairs, on=["query", "user_id"])
        test_df = df.merge(test_pairs, on=["query", "user_id"])
        return train_df, test_df

    @staticmethod
    def compute_tfidf_sim(vectorizer, row):
        q_vec = vectorizer.transform([row["query"]])
        d_vec = vectorizer.transform([row["doc"]])
        return cosine_similarity(q_vec, d_vec)[0, 0]

    @staticmethod
    def word_overlap(q, d):
        q_words = set(re.findall(r"\w+", q.lower()))
        d_words = set(re.findall(r"\w+", d.lower()))
        if not q_words:
            return 0.0
        return len(q_words & d_words) / len(q_words)

    @staticmethod
    def discretize_per_group(df):
        def bin_scores(scores):
            n = scores.nunique()
            if n == 1:
                return pd.Series(
                    [0] * len(scores), index=scores.index
                )  # all same label
            q = min(5, n)  # at most number of unique values
            return pd.qcut(scores, q=q, labels=False, duplicates="drop")

        df["rel_label"] = df.groupby(["query", "user_id"], group_keys=False)[
            "score"
        ].apply(bin_scores)
        return df

    def process_data(self):

        feature_cols = []
        target_col = ""

        try:

            rows = self.fetch_psql_data()
            df = self.psql_to_df(rows)

            train_df, test_df = self.split_query_user(df)

            # ---- TEXT FEATURES ----
            vectorizer = TfidfVectorizer(stop_words="english")
            vectorizer.fit(pd.concat([train_df["query"], train_df["doc"]]))

            train_df["tfidf_sim"] = train_df.apply(
                lambda row: self.compute_tfidf_sim(vectorizer, row), axis=1
            )
            test_df["tfidf_sim"] = test_df.apply(
                lambda row: self.compute_tfidf_sim(vectorizer, row), axis=1
            )

            feature_cols.append("tfidf_sim")

            train_df["word_overlap"] = train_df.apply(
                lambda row: self.word_overlap(row["query"], row["doc"]), axis=1
            )
            test_df["word_overlap"] = test_df.apply(
                lambda row: self.word_overlap(row["query"], row["doc"]), axis=1
            )

            feature_cols.append("word_overlap")

            train_df["jaccard_similarity"] = train_df.apply(
                lambda row: self.jaccard_similarity(row["query"], row["doc"]), axis=1
            )
            test_df["jaccard_similarity"] = test_df.apply(
                lambda row: self.jaccard_similarity(row["query"], row["doc"]), axis=1
            )

            feature_cols.append("jaccard_similarity")

            # ---- USER FEATURES ----
            train_df["persona_enc"] = (
                train_df["user_persona"].astype("category").cat.codes
            )
            test_df["persona_enc"] = (
                test_df["user_persona"].astype("category").cat.codes
            )

            feature_cols.append("persona_enc")

            train_df["expertise_enc"] = (
                train_df["user_expertise"].astype("category").cat.codes
            )
            test_df["expertise_enc"] = (
                test_df["user_expertise"].astype("category").cat.codes
            )

            feature_cols.append("expertise_enc")

            train_df = self.discretize_per_group(train_df)
            test_df = self.discretize_per_group(test_df)

            target_col = "rel_label"

            if os.path.exists("artifacts"):
                self.logger.info("Folder artifacts exists, trying to save tf idf")
                self.save_tfidf_vectorizer(vectorizer, "artifacts/tfidf_vectorizer.pkl")
            else:
                self.logger.warning(
                    "Folder artifacts does not exist, could not save tf idf"
                )

            self.logger.info(f"Feature cols: {feature_cols}")
            self.logger.info(f"Target col: {target_col}")

            self.save_metadata(train_df, feature_cols, artifacts_dir="artifacts")

            return train_df, test_df, feature_cols, target_col

        except Exception as e:
            self.logger.error(f"Error: {e}")
            raise e
