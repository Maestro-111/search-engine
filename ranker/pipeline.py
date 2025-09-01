from data_prep import DataPrep
import xgboost as xgb
import pandas as pd
from sklearn.metrics import ndcg_score


def evaluate_per_query(
    model, df, feature_cols, target_col, group_key=("query", "user_id"), k=5
):
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
        )

        train_df, test_df, feature_cols, target_col = prep.process_data()

        X_train = train_df[feature_cols].values
        y_train = train_df[target_col].values
        X_test = test_df[feature_cols].values
        y_test = test_df[target_col].values

        # Grouping: number of docs per (query, user_id)
        train_group = train_df.groupby(["query", "user_id"]).size().to_numpy()
        test_group = test_df.groupby(["query", "user_id"]).size().to_numpy()

        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtrain.set_group(train_group)

        dtest = xgb.DMatrix(X_test, label=y_test)
        dtest.set_group(test_group)

        params = {
            "objective": "rank:ndcg",  # optimize ranking
            "eval_metric": "ndcg",
            "eta": 0.1,
            "max_depth": 6,
            "min_child_weight": 100,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        }

        model = xgb.train(
            params,
            dtrain,
            num_boost_round=200,
            evals=[(dtrain, "train"), (dtest, "test")],
            early_stopping_rounds=20,
        )

        test_df["pred"] = model.predict(dtest)
        test_df["rank"] = test_df.groupby(["query", "user_id"])["pred"].rank(
            "dense", ascending=False
        )

        train_eval = evaluate_per_query(model, train_df, feature_cols, target_col, k=5)
        test_eval = evaluate_per_query(model, test_df, feature_cols, target_col, k=5)

        print("Train NDCG@5 (mean):", train_eval["ndcg"].mean())
        print("Test NDCG@5 (mean):", test_eval["ndcg"].mean())

        test_eval.to_csv("test_ndcg_per_query.csv", index=False)

    except Exception as e:
        raise e


if __name__ == "__main__":
    main()
