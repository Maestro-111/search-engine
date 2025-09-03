from data_prep import DataPrep
import xgboost as xgb
import pandas as pd
from sklearn.metrics import ndcg_score
from ranker_logging import logger
from xgb_ranker import train_xgb_ranker


def evaluate_per_query(model, df, feature_cols, target_col, k, group_key):
    """
    Compute NDCG@k per query-user group.
    """
    results = []

    for (q, u), group in df.groupby(group_key):

        if len(group) < 2:
            continue

        X = group[feature_cols].values
        y_true = group[target_col].values
        y_pred = model.predict(xgb.DMatrix(X))

        # ndcg_score expects shape (1, n_docs) or (n_queries, n_docs)
        ndcg = ndcg_score([y_true], [y_pred], k=k)
        results.append({"query": q, "user_id": u, "ndcg": ndcg})

    return pd.DataFrame(results)


def main():

    try:

        prep = DataPrep(
            "user_trainingdata",
            host="db",
            port=5432,
            dbname="search_db",
            user="search_admin",
            password="1234",
            logger=logger,
        )

        train_df, test_df, feature_cols, target_col = prep.process_data()

        model = train_xgb_ranker(
            train_df, test_df, feature_cols, target_col, logger=logger
        )

        train_eval = evaluate_per_query(
            model, train_df, feature_cols, target_col, 5, ["query", "user_id"]
        )
        test_eval = evaluate_per_query(
            model, test_df, feature_cols, target_col, 5, ["query", "user_id"]
        )

        logger.info(f"Train NDCG@5 (mean): {train_eval["ndcg"].mean()}")
        logger.info(f"Test NDCG@5 (mean): {test_eval["ndcg"].mean()}")

        test_eval.to_csv("test_ndcg_per_query.csv", index=False)

    except Exception as e:
        logger.error(f"Pipeline Error: {e}")
        raise e


if __name__ == "__main__":
    main()
