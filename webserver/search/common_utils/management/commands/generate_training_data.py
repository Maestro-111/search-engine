# management/commands/generate_training_data.py

from django.core.management.base import BaseCommand
from django.db import transaction
from user.models import SyntheticUser, TrainingData
from source_wikipedia.utils.elastic_wiki import WikipediaElastic
from common_utils.management.commands.generate_synthetic_users import (
    EntityGenerator,
    QueryFromEntityGenerator,
)
from django.db.models import Avg
import math
import random
import logging
from django.db import models


logger = logging.getLogger("create_training_data")


class SyntheticRelevanceCalculator:
    """Calculate synthetic relevance scores for training data"""

    def calculate_synthetic_relevance(self, user, entity, document, rank):
        """
        Calculate a synthetic relevance score (0-1) based on multiple factors

        Args:
            user: SyntheticUser instance
            entity: Dict with search entity (title, content_keywords, categories)
            document: Dict with document data from Elasticsearch
            rank: Position in search results (0-based)

        Returns:
            float: Relevance score between 0 and 1
        """

        score_components = {
            "preference_match": self._calculate_preference_match(user, document),
            "query_document_match": self._calculate_query_document_match(
                entity, document
            ),
            "position_bias": self._calculate_position_bias(rank),
            "category_overlap": self._calculate_category_overlap(user, document),
        }

        # Weight the components based on user persona
        weights = self._get_weights_for_persona(user.persona)

        # Calculate weighted sum
        total_score = sum(
            score_components[component] * weights.get(component, 0.1)
            for component in score_components
        )

        # Add noise for realism (real users aren't perfectly predictable)
        noise = random.gauss(0, 0.05)
        total_score += noise

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, total_score))

    def _calculate_preference_match(self, user, document):
        """Calculate how well document matches user preferences"""
        score = 0.0
        matches = 0
        total_weights = 0

        # Get user preferences
        user_prefs = user.preferences.all()

        # Check title matches
        title_prefs = user_prefs.filter(preference_type="title")
        doc_title = document.get("title", "").lower()

        for pref in title_prefs:
            if pref.preference_value.lower() in doc_title:
                score += pref.weight
                matches += 1
            total_weights += pref.weight

        # Check content keyword matches
        keyword_prefs = user_prefs.filter(preference_type="content_keywords")
        doc_content = document.get("excerpt", "").lower()

        for pref in keyword_prefs:
            if (
                pref.preference_value.lower() in doc_content
                or pref.preference_value.lower() in doc_title
            ):
                score += (
                    pref.weight * 0.7
                )  # Keywords in content are slightly less important
                matches += 1
            total_weights += pref.weight

        # Normalize by total weights
        if total_weights > 0:
            return score / total_weights
        return 0.0

    def _calculate_query_document_match(self, entity, document):
        """Calculate how well document matches the search entity"""
        score = 0.0

        # Title match (highest weight)
        if entity.get("title"):
            doc_title = document.get("title", "").lower()
            entity_title = entity["title"].lower()

            if entity_title == doc_title:
                score += 0.5
            elif entity_title in doc_title or doc_title in entity_title:
                score += 0.3
            elif any(word in doc_title for word in entity_title.split()):
                score += 0.1

        # Keyword matches
        if entity.get("content_keywords"):
            doc_content = (
                document.get("excerpt", "") + " " + document.get("title", "")
            ).lower()
            matching_keywords = sum(
                1
                for keyword in entity["content_keywords"]
                if keyword.lower() in doc_content
            )
            if entity["content_keywords"]:
                score += (matching_keywords / len(entity["content_keywords"])) * 0.3

        # Category matches
        if entity.get("categories") and document.get("categories"):
            doc_categories = [cat.lower() for cat in document["categories"]]
            entity_categories = [cat.lower() for cat in entity["categories"]]

            matching_categories = sum(
                1
                for cat in entity_categories
                if any(cat in doc_cat or doc_cat in cat for doc_cat in doc_categories)
            )
            if entity_categories:
                score += (matching_categories / len(entity_categories)) * 0.2

        return score

    def _calculate_position_bias(self, rank):
        """Calculate position bias - higher ranks get lower scores"""
        # Use logarithmic decay - typical user behavior
        # Position 0: 1.0, Position 1: ~0.63, Position 5: ~0.31, Position 10: ~0.21
        return 1.0 / (1.0 + math.log(rank + 1))

    def _calculate_category_overlap(self, user, document):
        """Calculate overlap between user's preferred categories and document categories"""
        if not document.get("categories"):
            return 0.0

        # Get user's category preferences
        user_categories = set(
            user.preferences.filter(preference_type="categories").values_list(
                "preference_value", flat=True
            )
        )

        if not user_categories:
            return 0.5  # Neutral if user has no category preferences

        # Calculate overlap
        doc_categories = set(cat.lower() for cat in document["categories"])
        user_categories_lower = set(cat.lower() for cat in user_categories)

        # Check for exact and partial matches
        exact_matches = len(doc_categories & user_categories_lower)
        partial_matches = sum(
            1
            for doc_cat in doc_categories
            for user_cat in user_categories_lower
            if (user_cat in doc_cat or doc_cat in user_cat) and doc_cat != user_cat
        )

        total_matches = exact_matches + (partial_matches * 0.5)
        return min(1.0, total_matches / len(user_categories))

    def _get_weights_for_persona(self, persona):
        """Get component weights based on user persona"""
        weights = {
            "developer": {
                "preference_match": 0.25,
                "query_document_match": 0.3,
                "position_bias": 0.15,
                "category_overlap": 0.1,
            },
            "data_scientist": {
                "preference_match": 0.2,
                "query_document_match": 0.35,
                "position_bias": 0.15,
                "category_overlap": 0.05,
            },
            "business_analyst": {
                "preference_match": 0.3,
                "query_document_match": 0.25,
                "position_bias": 0.2,
                "category_overlap": 0.1,
            },
            "researcher": {
                "preference_match": 0.25,
                "query_document_match": 0.3,
                "position_bias": 0.1,
                "category_overlap": 0.15,
            },
            "student": {
                "preference_match": 0.2,
                "query_document_match": 0.25,
                "position_bias": 0.25,
                "category_overlap": 0.05,
            },
            "historian": {
                "preference_match": 0.3,
                "query_document_match": 0.35,
                "position_bias": 0.1,
                "category_overlap": 0.1,
            },
            "hr": {
                "preference_match": 0.3,
                "query_document_match": 0.25,
                "position_bias": 0.12,
                "category_overlap": 0.1,
            },
            "marketing": {
                "preference_match": 0.2,
                "query_document_match": 0.2,
                "position_bias": 0.1,
                "category_overlap": 0.1,
            },
            "finance": {
                "preference_match": 0.3,
                "query_document_match": 0.35,
                "position_bias": 0.1,
                "category_overlap": 0.1,
            },
            "designer": {
                "preference_match": 0.2,
                "query_document_match": 0.2,
                "position_bias": 0.15,
                "category_overlap": 0.1,
            },
            "healthcare": {
                "preference_match": 0.4,
                "query_document_match": 0.4,
                "position_bias": 0.05,
                "category_overlap": 0.1,
            },
            "educator": {
                "preference_match": 0.4,
                "query_document_match": 0.4,
                "position_bias": 0.2,
                "category_overlap": 0.1,
            },
        }

        return weights.get(persona, weights["developer"])


class Command(BaseCommand):
    help = "Generate synthetic training data for ranking model"

    wiki_elastic_client = WikipediaElastic(logger)
    entity_generator = EntityGenerator()
    query_generator = QueryFromEntityGenerator()
    relevance_calculator = SyntheticRelevanceCalculator()

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing training data before generating new data",
        )
        parser.add_argument(
            "--entities-per-user",
            type=int,
            default=1,
            help="Number of entities to generate per user",
        )

    def handle(self, *args, **kwargs):
        # Clear existing data if requested
        if kwargs.get("clear"):
            self.stdout.write("Clearing existing training data...")
            TrainingData.objects.all().delete()

        training_data_batch = []
        batch_size = 500  # Save in batches for better performance
        total_created = 0
        entities_per_user = kwargs.get("entities_per_user", 1)

        users = SyntheticUser.objects.all()
        total_users = users.count()

        for user_idx, user in enumerate(users):
            self.stdout.write(
                f"Processing user {user_idx + 1}/{total_users}: {user.name}"
            )

            entities = self.entity_generator.generate_entities_for_user(
                user, num_entities=entities_per_user
            )

            for entity in entities:
                print(f"Entity: {entity}")

                query = self.query_generator.generate_query_from_entity(entity, user)

                search_body = self.wiki_elastic_client.build_elasticsearch_query_wiki(
                    entity
                )
                results = self.wiki_elastic_client.query_specified_fields(
                    search_body, "wikipedia"
                )

                # Process top 10 results
                for rank, document in enumerate(results[:10]):
                    relevance = self.relevance_calculator.calculate_synthetic_relevance(
                        user, entity, document, rank
                    )

                    training_data_batch.append(
                        TrainingData(
                            user=user,
                            query=query,
                            entity=entity,
                            doc_url=document.get("url", ""),
                            doc_title=document["title"],
                            relevance_score=relevance,
                            rank=rank,
                            user_persona=user.persona,
                            user_expertise=user.expertise_level,
                        )
                    )

                    if len(training_data_batch) >= batch_size:
                        with transaction.atomic():
                            TrainingData.objects.bulk_create(training_data_batch)
                            total_created += len(training_data_batch)
                            self.stdout.write(f"  Saved {total_created} records...")
                            training_data_batch = []

        if training_data_batch:
            with transaction.atomic():
                TrainingData.objects.bulk_create(training_data_batch)
                total_created += len(training_data_batch)

        # Print summary statistics
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully generated {total_created} training examples"
            )
        )

        # Show some statistics
        stats = TrainingData.objects.aggregate(
            avg_relevance=Avg("relevance_score"), total=models.Count("id")
        )

        self.stdout.write("\nTraining Data Statistics:")
        self.stdout.write(f"  Total records: {stats['total']}")
        self.stdout.write(f"  Average relevance score: {stats['avg_relevance']:.3f}")
        self.stdout.write(f"  Records per user: {total_created / total_users:.1f}")

        # Show distribution by rank
        self.stdout.write("\nRelevance by rank position:")
        for rank in range(10):
            avg_rel = TrainingData.objects.filter(rank=rank).aggregate(
                avg=Avg("relevance_score")
            )["avg"]
            if avg_rel:
                self.stdout.write(f"  Rank {rank}: {avg_rel:.3f}")
