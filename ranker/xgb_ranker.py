import xgboost as xgb


def train_xgb_ranker(train_df, test_df, feature_cols, target_col, logger):

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
        "objective": "rank:ndcg",
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

    logger.info("Done Training")

    feature_importance = model.get_score(importance_type="gain")
    logger.info(f"Feature importance: {feature_importance}")

    model.save_model("artifacts/xgb_ranker.json")
    logger.info("Saved Model")

    return model
