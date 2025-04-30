from elasticsearch import Elasticsearch
import os
import logging

logger = logging.getLogger("webserver")

class QueryElastic:

    def __init__(self):
        self.es = Elasticsearch([os.environ.get('ELASTICSEARCH_URI', 'http://elasticsearch:9200')])

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

        # Process the results
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
                # Extract title from URL if possible
                url = source.get("url", "")
                if "wikipedia.org/wiki/" in url:
                    # Extract the title from the URL
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


    def query_specified_fields(self, query):

        """
        Determine the entities and use them separately to query
        """

        pass