from elasticsearch import Elasticsearch
import os
import logging
import openai
import json

logger = logging.getLogger("webserver")

class QueryElastic:

    def __init__(self):

        self.es = Elasticsearch([os.environ.get('ELASTICSEARCH_URI', 'http://elasticsearch:9200')])
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def query_general(self, query):

        """
        Query all fields.
        """

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

        try:
            search_results = self.es.search(index="wikipedia", body=search_body)
        except Exception as e:
            logger.error(e)
            return []

        return self.process_elastic_response(search_results)


    def extract_entities_with_openai(self, query):
        """
        Use OpenAI to extract structured entities from the user query
        """
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

        try:
            response = openai.chat.completions.create(
                model="gpt-4",  # Or your preferred model
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse the JSON response
            extracted_data = json.loads(response.choices[0].message.content)
            logger.info(f"Extracted entities: {extracted_data}")
            return extracted_data

        except Exception as e:
            logger.error(f"Error extracting entities with LLM: {e}")
            return {
                "title": None,
                "content_keywords": [],
                "categories": [],
                "link_related": []
            }


    def process_elastic_response(self, search_results):

        raw_results = []

        for hit in search_results["hits"]["hits"]:

            source = hit["_source"]
            highlight = hit.get("highlight", {})

            #Get excerpt from highlights or summary
            if "summary" in highlight:
                excerpt = "...".join(highlight["summary"])
            elif "content" in highlight:
                excerpt = "...".join(highlight["content"][:1])
            else:
                excerpt = source.get("summary", "")[:200] + "..."

                # Get first category or empty string
            categories = []
            if source.get("categories"):
                categories = source["categories"][:5]

            title = source.get("title")
            if title is None:

                url = source.get("url", "")
                if "wikipedia.org/wiki/" in url:
                    title = url.split("/wiki/")[-1].replace("_", " ")
                else:
                    title = "Untitled Document"

            raw_results.append({
                "title": title,
                "url": source["url"],
                "excerpt": excerpt,
                "categories": categories,
                "last_updated": "N/A"  # Placeholder
            })

        return raw_results


    def build_elasticsearch_query(self, entities):
        """
        Build an Elasticsearch query using the extracted entities
        """
        should_clauses = []
        must_clauses = []

        # Title field is highly weighted
        if entities.get("title"):
            must_clauses.append({
                "match_phrase": {
                    "title": {
                        "query": entities["title"],
                        "boost": 5  # Higher boost for title matches
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

        # Categories
        if entities.get("categories") and len(entities["categories"]) > 0:
            category_queries = []
            for category in entities["categories"]:
                category_queries.append({"match": {"categories": category}})
            should_clauses.append({"bool": {"should": category_queries}})

        # Link-related topics
        if entities.get("link_related") and len(entities["link_related"]) > 0:
            link_queries = []
            for link_topic in entities["link_related"]:
                link_queries.append({"match": {"link_texts": link_topic}})
            should_clauses.append({"bool": {"should": link_queries}})

        # Build the complete query structure
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}],
                "should": should_clauses,
                "minimum_should_match": 1 if should_clauses and not must_clauses else 0
            }
        }

        # Construct the full search body
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

        logger.debug(f"Built Elasticsearch query: {json.dumps(search_body, indent=2)}")
        return search_body

    def query_specified_fields(self, query):
        """
        Determine the entities and use them separately to query
        """
        # Step 1: Extract entities from query using LLM
        entities = self.extract_entities_with_openai(query)

        # Step 2: Build the Elasticsearch query based on entities
        search_body = self.build_elasticsearch_query(entities)

        # Step 3: Execute the search
        try:
            search_results = self.es.search(index="wikipedia", body=search_body)
        except Exception as e:
            logger.error(f"Error executing Elasticsearch query: {e}")
            return []

        return self.process_elastic_response(search_results)