# management/commands/generate_training_data.py
from django.core.management.base import BaseCommand
from users.models import SyntheticUser
from .generate_synthetic_users import EntityGenerator, QueryFromEntityGenerator
from source_wikipedia.utils import WikipediaElastic
import json


class Command(BaseCommand):

    help = "Generate synthetic training data for ranking model"
    wiki_elastic_client = WikipediaElastic()

    def handle(self, *args, **kwargs):

        entity_generator = EntityGenerator()
        query_generator = QueryFromEntityGenerator()

        training_data = []

        for user in SyntheticUser.objects.all():
            entities = entity_generator.generate_entities_for_user(user, num_queries=20)

            for entity in entities:

                query = query_generator.generate_query_from_entity(entity)

                search_body = self.wiki_elastic_client.build_elasticsearch_query_wiki(
                    entity
                )
                results = self.wiki_elastic_client.query_specified_fields(
                    search_body, "wikipedia"
                )

                for rank, hit in enumerate(results["hits"]["hits"]):
                    relevance = self.calculate_synthetic_relevance(
                        user, query, hit, rank
                    )

                    training_data.append(
                        {
                            "user_id": user.id,
                            "query": query,
                            "doc_id": hit["_id"],
                            "relevance_score": relevance,
                            "features": {
                                "es_score": hit["_score"],
                                "rank": rank,
                                "user_expertise": user.expertise_level,
                                # Add more features
                            },
                        }
                    )

        # Save to file or database
        with open("training_data.json", "w") as f:
            json.dump(training_data, f)

        self.stdout.write(
            self.style.SUCCESS(f"Generated {len(training_data)} training examples")
        )
