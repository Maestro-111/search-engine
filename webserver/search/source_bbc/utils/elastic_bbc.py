import json
from common_utils.elastic_agent import BaseElastic


class BBCElastic(BaseElastic):

    def generate_regular_search_body_wiki(self, query):

        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "title^3",
                                    "summary^2",
                                    "content",
                                    "link_texts",
                                ],
                            }
                        }
                    ]
                }
            },
            "highlight": {"fields": {"summary": {}, "content": {}}},
            "size": 100,
        }

        return search_body

    def generate_prompt_wiki(self, query):

        prompt = f"""
        Extract search entities from the user's query for a BBC search engine that uses this Elasticsearch index:

        Index Fields:
        - url: Website URL (keyword type)
        - title: Article title (text type with English analyzer)
        - summary: Article summary (text type with English analyzer)
        - content: Main article content (text type with English analyzer)

        User Query: "{query}"

        Your task:
        Identify key terms or phrases from the query and map them to our index fields:
        - "title": Main topic or named entity likely to appear in the article title
        - "content_keywords" : Extract important keywords that should be searched in the content and summary fields

        Format the response as a JSON object with these fields. If a field is not applicable, use an empty list or null.
        Example query: "articles about battle of kursk involving tanks"
        Example response:
        {{
            "title": "Battle of Kursk",
            "content_keywords": ["tank", "tanks", "involving"],
        }}

        Another example query: "physics discoveries by Einstein related to relativity"
        Example response:
        {{
            "title": "Albert Einstein",
            "content_keywords": ["physics", "discoveries", "relativity"],
        }}

        Ensure your extraction matches the semantic structure of our Elasticsearch index to optimize search results.
        """

        self.logger.info("Built BBC prompt")

        return prompt

    def build_elasticsearch_query_wiki(self, entities):
        """
        Build an Elasticsearch query using the extracted entities
        """
        should_clauses = []
        must_clauses = []

        if entities.get("title"):
            must_clauses.append(
                {"match_phrase": {"title": {"query": entities["title"], "boost": 5}}}
            )

        # Content keywords
        if entities.get("content_keywords") and len(entities["content_keywords"]) > 0:
            for keyword in entities["content_keywords"]:
                should_clauses.append(
                    {
                        "multi_match": {
                            "query": keyword,
                            "fields": ["content^2", "summary^3"],
                            "type": "phrase",
                        }
                    }
                )

        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "should": should_clauses,
                "minimum_should_match": 1 if should_clauses and not must_clauses else 0,
            }
        }

        search_body = {
            "query": query,
            "highlight": {"fields": {"summary": {}, "content": {}}},
            "size": 100,
        }

        self.logger.info(
            f"Built BBC Elasticsearch query: {json.dumps(search_body, indent=2)}"
        )
        return search_body
