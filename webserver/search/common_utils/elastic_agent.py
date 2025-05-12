from elasticsearch import Elasticsearch
import os
import openai
import json

class BaseElastic:

    def __init__(self, logger):

        self.es = Elasticsearch([os.environ.get('ELASTICSEARCH_URI', 'http://elasticsearch:9200')])
        self.logger = logger
        openai.api_key = os.environ.get("OPENAI_API_KEY")


    def extract_entities_with_openai(self, prompt):

        """
        Use OpenAI to extract structured entities from the user query
        """

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )

            extracted_data = json.loads(response.choices[0].message.content)
            self.logger.info(f"Extracted entities: {extracted_data}")
            return extracted_data

        except Exception as e:
            self.logger.error(f"Error extracting entities with LLM: {e}")
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

            # Get excerpt from highlights or summary
            if "summary" in highlight:
                excerpt = "...".join(highlight["summary"])
            elif "content" in highlight:
                excerpt = "...".join(highlight["content"][:1])
            else:
                excerpt = source.get("summary", "")[:200] + "..."

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
                "last_updated": "N/A"
            })

        if raw_results:
            self.logger.info(f"Processed {len(raw_results)} results")
            self.logger.info(f"Raw results: {raw_results[0]}")
        else:
            self.logger.warn("No results")


        return raw_results

    def query_specified_fields(self, search_body, index):

        """
        Determine the entities and use them separately to query
        """

        try:
            search_results = self.es.search(index=index, body=search_body)
        except Exception as e:
            self.logger.error(f"Error executing Elasticsearch query: {e}")
            return []

        return self.process_elastic_response(search_results)


