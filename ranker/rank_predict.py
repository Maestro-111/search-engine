import argparse
import pickle
import pandas as pd
import xgboost as xgb
import re
from sklearn.metrics.pairwise import cosine_similarity
import os
import json
from ranker_logging import logger


def compute_tfidf_sim(vectorizer, query, document):
    """Compute TF-IDF similarity between query and document"""
    q_vec = vectorizer.transform([query])
    d_vec = vectorizer.transform([document])
    return cosine_similarity(q_vec, d_vec)[0, 0]


def word_overlap(query, document):
    """Calculate word overlap between query and document"""
    q_words = set(re.findall(r"\w+", query.lower()))
    d_words = set(re.findall(r"\w+", document.lower()))
    if not q_words:
        return 0.0
    return len(q_words & d_words) / len(q_words)


def jaccard_similarity(query, document):
    """Calculate Jaccard similarity between query and document"""
    q_words = set(re.findall(r"\w+", query.lower()))
    d_words = set(re.findall(r"\w+", document.lower()))
    if not q_words and not d_words:
        return 0.0
    return len(q_words & d_words) / len(q_words | d_words)


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


def prepare_features(
    user_persona, user_expertise, query, document, tf_idf_vectorizer, metadata=None
):
    """
    Prepare features for a single prediction

    Args:
        user_persona: User persona string
        user_expertise: User expertise string
        query: Query string
        document: Document string
        tf_idf_vectorizer: Loaded TF-IDF vectorizer
        metadata: Optional metadata containing category mappings

    Returns:
        DataFrame with features ready for prediction
    """

    # Create a single-row dataframe
    data = {
        "user_persona": [user_persona],
        "user_expertise": [user_expertise],
        "query": [query],
        "doc": [document],
    }
    df = pd.DataFrame(data)

    # Feature columns list (must match training)
    feature_cols = []

    # ---- TEXT FEATURES ----

    # TF-IDF similarity
    df["tfidf_sim"] = compute_tfidf_sim(tf_idf_vectorizer, query, document)
    feature_cols.append("tfidf_sim")

    # Word overlap
    df["word_overlap"] = word_overlap(query, document)
    feature_cols.append("word_overlap")

    # Jaccard similarity
    df["jaccard_similarity"] = jaccard_similarity(query, document)
    feature_cols.append("jaccard_similarity")

    # ---- USER FEATURES ----

    # Handle persona encoding
    if metadata and "persona_categories" in metadata:
        # Use saved categories from training
        persona_cats = metadata["persona_categories"]
        if user_persona in persona_cats:
            df["persona_enc"] = persona_cats.index(user_persona)
        else:
            logger.warning(f"Unknown persona '{user_persona}', using default value -1")
            df["persona_enc"] = -1
    else:
        # Fallback: simple hash-based encoding
        df["persona_enc"] = hash(user_persona) % 100
        logger.warning("No persona categories found in metadata, using hash encoding")

    feature_cols.append("persona_enc")

    # Handle expertise encoding
    if metadata and "expertise_categories" in metadata:
        # Use saved categories from training
        expertise_cats = metadata["expertise_categories"]
        if user_expertise in expertise_cats:
            df["expertise_enc"] = expertise_cats.index(user_expertise)
        else:
            logger.warning(
                f"Unknown expertise '{user_expertise}', using default value -1"
            )
            df["expertise_enc"] = -1
    else:
        # Fallback: simple hash-based encoding
        df["expertise_enc"] = hash(user_expertise) % 100
        logger.warning("No expertise categories found in metadata, using hash encoding")

    feature_cols.append("expertise_enc")

    logger.info(f"Prepared features: {feature_cols}")

    return df[feature_cols]


def predict_rank(
    user_persona, user_expertise, query, document, artifacts_dir="artifacts"
):
    """
    Main prediction function

    Args:
        user_persona: User persona string
        user_expertise: User expertise string
        query: Query string
        document: Document string
        artifacts_dir: Directory containing saved artifacts

    Returns:
        dict: Prediction results including score and confidence
    """

    try:
        # Load artifacts
        tf_idf_vectorizer, xgb_model, metadata = load_artifacts(artifacts_dir)

        # Prepare features
        features_df = prepare_features(
            user_persona, user_expertise, query, document, tf_idf_vectorizer, metadata
        )

        # Make prediction - Fixed version
        # Convert to numpy array
        features_array = features_df.values

        # Create DMatrix
        dmatrix = xgb.DMatrix(features_array)

        # Predict
        score = xgb_model.predict(dmatrix)[0]

        # Prepare response
        result = {
            "score": float(score),
            "inputs": {
                "user_persona": user_persona,
                "user_expertise": user_expertise,
                "query": query,
                "document": document[:100] + "..." if len(document) > 100 else document,
            },
            "features": features_df.to_dict("records")[0],
            "status": "success",
        }

        logger.info(f"Prediction successful: score={score:.4f}")
        return result

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"score": None, "error": str(e), "status": "failed"}


def main():
    """Main entry point with argparse"""

    parser = argparse.ArgumentParser(
        description="Predict ranking score for query-document pair with user context"
    )

    parser.add_argument(
        "--user_persona",
        type=str,
        required=True,
        help='User persona (e.g., "researcher", "student", "professional")',
    )

    parser.add_argument(
        "--user_expertise",
        type=str,
        required=True,
        help='User expertise level (e.g., "beginner", "intermediate", "expert")',
    )

    parser.add_argument("--query", type=str, required=True, help="Search query string")

    parser.add_argument(
        "--document", type=str, required=True, help="Document content to rank"
    )

    parser.add_argument(
        "--artifacts_dir",
        type=str,
        default="artifacts",
        help="Directory containing model artifacts (default: artifacts)",
    )

    parser.add_argument(
        "--output_format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    # Run prediction
    result = predict_rank(
        user_persona=args.user_persona,
        user_expertise=args.user_expertise,
        query=args.query,
        document=args.document,
        artifacts_dir=args.artifacts_dir,
    )

    # Output results
    if args.output_format == "json":
        import json

        print(json.dumps(result, indent=2))
    else:
        if result["status"] == "success":
            logger.info("\n✓ Ranking Prediction Results:")
            logger.info(f"  Score: {result['score']:.4f}")
            logger.info("\nInputs:")
            logger.info(f"  User Persona: {result['inputs']['user_persona']}")
            logger.info(f"  User Expertise: {result['inputs']['user_expertise']}")
            logger.info(f"  Query: {result['inputs']['query']}")
            logger.info(f"  Document: {result['inputs']['document']}")
            logger.info("\nFeature Values:")
            for feat, val in result["features"].items():
                logger.info(
                    f"  {feat}: {val:.4f}"
                    if isinstance(val, float)
                    else f"  {feat}: {val}"
                )
        else:
            logger.info("\n✗ Prediction Failed:")
            logger.info(f"  Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
