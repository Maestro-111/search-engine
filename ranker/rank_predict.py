import pickle
import pandas as pd
import xgboost as xgb
import os
from ranker_logging import logger
import json
from data_prep import DataPrep


class WrapDataPrep(DataPrep):
    def __init__(self, logger):
        self.logger = logger


def load_artifacts(artifacts_dir="artifacts"):
    """Load saved TF-IDF vectorizer and XGBoost model"""

    # Load TF-IDF vectorizer
    vectorizer_path = os.path.join(artifacts_dir, "tfidf_vectorizer.pkl")
    try:
        with open(vectorizer_path, "rb") as f:
            tf_idf_vectorizer = pickle.load(f)
        logger.info(f"Successfully loaded TF-IDF vectorizer from {vectorizer_path}")
    except Exception as e:
        logger.error(f"Failed to load TF-IDF vectorizer: {e}")
        raise e

    # Load XGBoost model - Load as Booster, not XGBRanker
    model_path = os.path.join(artifacts_dir, "xgb_ranker.json")
    try:
        # Load as Booster since you trained with xgb.train()
        xgb_model = xgb.Booster()
        xgb_model.load_model(model_path)
        logger.info(f"Successfully loaded XGBoost model from {model_path}")
    except Exception as e:
        logger.error(f"Failed to load XGBoost model: {e}")
        raise e

    # Load metadata if exists
    metadata_path = os.path.join(artifacts_dir, "metadata.json")
    metadata = {}
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            logger.info(f"Successfully loaded metadata from {metadata_path}")
        except Exception as e:
            logger.warning(f"Could not load metadata: {e}")

    return tf_idf_vectorizer, xgb_model, metadata


def predict_rank_multiple(
    user_persona, user_expertise, query, documents, artifacts_dir="artifacts"
):
    """
    Predict ranking scores for multiple documents

    Args:
        user_persona: User persona string
        user_expertise: User expertise string
        query: Query string
        documents: List of document strings
        artifacts_dir: Directory containing saved artifacts

    Returns:
        dict: Prediction results with scores for all documents
    """

    try:
        # Load artifacts once

        data_prep = WrapDataPrep(logger)
        tf_idf_vectorizer, xgb_model, metadata = load_artifacts(artifacts_dir)

        results = []

        # Process each document
        for doc_idx, document in enumerate(documents):
            # Prepare features for this document

            data = {
                "user_persona": [user_persona],
                "user_expertise": [user_expertise],
                "query": [query],
                "doc": [document],
            }
            df = pd.DataFrame(data)

            features_df = data_prep.process_data_predict(
                df, tf_idf_vectorizer, metadata, user_persona, user_expertise
            )

            # Convert to numpy array
            features_array = features_df.values

            # Create DMatrix
            dmatrix = xgb.DMatrix(features_array)

            score = xgb_model.predict(dmatrix)[0]

            results.append(
                {
                    "document_id": doc_idx,
                    "document": (
                        document[:200] + "..." if len(document) > 200 else document
                    ),
                    "score": float(score),
                }
            )

        ranked_results = sorted(results, key=lambda x: x["score"], reverse=True)

        return {
            "status": "success",
            "query": query,
            "user_persona": user_persona,
            "user_expertise": user_expertise,
            "num_documents": len(documents),
            "ranked_documents": ranked_results,
        }

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"status": "failed", "error": str(e)}


def main(user_persona, user_expertise, query, documents, artifacts_dir="artifacts"):
    """Main entry point with argparse"""

    try:
        documents = json.loads(documents)
        if not isinstance(documents, list):
            raise ValueError("Documents must be a list")
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing documents JSON: {e}")
        return 1

    logger.info(f"Documents: {documents}, {len(documents)}")

    # Run prediction
    result = predict_rank_multiple(
        user_persona=user_persona,
        user_expertise=user_expertise,
        query=query,
        documents=documents,
        artifacts_dir=artifacts_dir,
    )

    return result
