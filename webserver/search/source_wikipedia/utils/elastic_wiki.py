import json
from common_utils.elastic_agent import BaseElastic


class WikipediaElastic(BaseElastic):

    def generate_regular_search_body_wiki(self, query):

        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {"multi_match": {
                            "query": query,
                            "fields": ["title^3", "summary^2", "content", "link_texts"]
                        }}
                    ]
                }
            },
            "highlight": {
                "fields": {
                    "summary": {},
                    "content": {}
                }
            },
            "size": 100
        }

        return search_body

    def generate_prompt_wiki(self, query):

        prompt = f"""
        Extract search entities from this query for a Wikipedia search engine with the following index structure:

        Index Fields:
        - url: Website URL (keyword type)
        - title: Article title (text type with English analyzer)
        - summary: Article summary (text type with English analyzer)
        - content: Main article content (text type with English analyzer)
        - categories: Article categories (keyword type)
        - link_urls: URLs of linked pages (keyword type)
        - link_texts: Anchor text of links (text type with English analyzer)

        Query: "{query}"

        For this query, identify the following entities that match our index structure:
        - title: Extract specific article titles or main topics that should be searched in the title field
        - content_keywords: Extract important keywords that should be searched in the content and summary fields
        - categories: Extract category names that should be matched exactly against the categories field
        - link_related: Extract names of related topics that might appear in link_texts field

        Format the response as a JSON object with these fields. If a field is not applicable, use an empty list or null.
        Example query: "articles about battle of kursk involving tanks"
        Example response:
        {{
            "title": "Battle of Kursk",
            "content_keywords": ["tank", "tanks", "involving"],
            "categories": ["World War II", "Military history", "Battles"],
            "link_related": ["Panzer", "T-34", "Soviet tanks", "German tanks"]
        }}

        Another example query: "physics discoveries by Einstein related to relativity"
        Example response:
        {{
            "title": "Albert Einstein",
            "content_keywords": ["physics", "discoveries", "relativity"],
            "categories": ["Physics", "Scientific discoveries", "Relativity"],
            "link_related": ["Theory of relativity", "Special relativity", "General relativity", "E=mc²"]
        }}

        Ensure your extraction matches the semantic structure of our Elasticsearch index to optimize search results.
        """

        self.logger.info("Built Wiki prompt")

        return prompt

    def build_elasticsearch_query_wiki(self, entities):

        """
        Build an Elasticsearch query using the extracted entities
        """
        should_clauses = []
        must_clauses = []

        if entities.get("title"):
            must_clauses.append({
                "match_phrase": {
                    "title": {
                        "query": entities["title"],
                        "boost": 5
                    }
                }
            })

        # Content keywords
        if entities.get("content_keywords") and len(entities["content_keywords"]) > 0:
            for keyword in entities["content_keywords"]:
                should_clauses.append({
                    "multi_match": {
                        "query": keyword,
                        "fields": ["content^2", "summary^3"],
                        "type": "phrase"
                    }
                })

        if entities.get("categories") and len(entities["categories"]) > 0:
            category_queries = []
            for category in entities["categories"]:
                category_queries.append({"match": {"categories": category}})
            should_clauses.append({"bool": {"should": category_queries}})

        if entities.get("link_related") and len(entities["link_related"]) > 0:
            link_queries = []
            for link_topic in entities["link_related"]:
                link_queries.append({"match": {"link_texts": link_topic}})
            should_clauses.append({"bool": {"should": link_queries}})

        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "should": should_clauses,
                "minimum_should_match": 1 if should_clauses and not must_clauses else 0
            }
        }

        search_body = {
            "query": query,
            "highlight": {
                "fields": {
                    "summary": {},
                    "content": {}
                }
            },
            "size": 100
        }

        self.logger.info(f"Built Wiki Elasticsearch query: {json.dumps(search_body, indent=2)}")
        return search_body
