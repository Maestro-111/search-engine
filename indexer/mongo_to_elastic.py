# search-engine/indexing/mongo_to_elastic.py
import argparse
import os
import pymongo
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError
import json
import time


def extract_title_from_url(url):
    """Extract a title from a Wikipedia URL by formatting the last path component."""
    try:
        # Extract the last part of the URL path (after the last slash)
        last_path_component = url.split('/')[-1]

        # Replace underscores with spaces and decode URL encoding
        from urllib.parse import unquote
        title = unquote(last_path_component.replace('_', ' '))

        return title
    except Exception as e:
        print(f"Error extracting title from URL {url}: {e}")
        return ""


def main():
    parser = argparse.ArgumentParser(description='Transfer data from MongoDB to Elasticsearch')

    parser.add_argument('--mongo-uri', type=str,
                        default=os.environ.get('MONGODB_URI', 'mongodb://localhost:27017'),
                        help='MongoDB connection URI')
    parser.add_argument('--mongo-db', type=str, default='wikipedia_db',
                        help='MongoDB database name')
    parser.add_argument('--mongo-collection', type=str, default='articles',
                        help='MongoDB collection name')
    parser.add_argument('--elastic-url', type=str,
                        default=os.environ.get('ELASTICSEARCH_URI', 'http://localhost:9200'),
                        help='Elasticsearch connection URL')
    parser.add_argument('--elastic-index', type=str, default='wikipedia',
                        help='Elasticsearch index name')
    parser.add_argument('--batch-size', type=int, default=100,
                        help='Batch size for indexing')

    args = parser.parse_args()

    # Connect to MongoDB
    try:
        print(f"Connecting to MongoDB at {args.mongo_uri}...")
        mongo_client = pymongo.MongoClient(args.mongo_uri)
        mongo_db = mongo_client[args.mongo_db]
        mongo_collection = mongo_db[args.mongo_collection]

        # Test MongoDB connection
        doc_count = mongo_collection.count_documents({})
        print(
            f"Successfully connected to MongoDB. Found {doc_count} documents in {args.mongo_db}.{args.mongo_collection}")

        # Sample one document to inspect structure
        sample_doc = mongo_collection.find_one()
        print("\nSample document structure:")
        for key, value in sample_doc.items():
            if key == '_id':
                print(f"_id: {value}")
            else:
                print(f"{key}: {type(value)}")
                if key == 'internal_links' and isinstance(value, list) and len(value) > 0:
                    print(f"  First internal_link item: {value[0]}")

    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return

    # Connect to Elasticsearch
    try:
        print(f"Connecting to Elasticsearch at {args.elastic_url}")
        es_client = Elasticsearch(args.elastic_url, request_timeout=30)

        # Test Elasticsearch connection
        es_info = es_client.info()
        print(f"Successfully connected to Elasticsearch {es_info['version']['number']}")
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {e}")
        return

    mapping = {
        "mappings": {
            "properties": {
                "url": {"type": "keyword"},
                "title": {"type": "text", "analyzer": "english"},
                "summary": {"type": "text", "analyzer": "english"},
                "content": {"type": "text", "analyzer": "english"},
                "categories": {"type": "keyword"},
                "link_urls": {"type": "keyword"},  # Store just the URLs as keywords
                "link_texts": {"type": "text", "analyzer": "english"}  # Store link texts for searching
            }
        },
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "mapping.ignore_malformed": True
            }
        }
    }

    # Create or update index
    index_name = args.elastic_index

    try:
        exists = es_client.indices.exists(index=index_name)
        print(f"Index {index_name} exists: {exists}")

        if exists:
            try:
                es_client.indices.put_mapping(index=index_name, body=mapping["mappings"])
                print(f"Updated mapping for index {index_name}")
            except Exception as e:
                print(f"Warning: Could not update mapping: {e}")
        else:
            try:
                es_client.indices.create(index=index_name, body=mapping)
                print(f"Index {index_name} created successfully")
            except Exception as e:
                print(f"Warning: Could not create mapping: {e}")

    except Exception as e:
        print(f"Error with index: {e}")
        return

    # Process documents in batches
    def process_in_batches(batch_size=args.batch_size):
        total_docs = mongo_collection.count_documents({})
        print(f"Processing {total_docs} documents in batches of {batch_size}")

        processed = 0
        successful = 0
        failed = 0

        for skip in range(0, total_docs, batch_size):

            batch = list(mongo_collection.find().skip(skip).limit(batch_size))
            actions = []

            for doc in batch:

                try:

                    doc_id = str(doc.pop('_id', ''))

                    link_urls = []
                    link_texts = []

                    internal_links = doc.get('internal_links', [])
                    if isinstance(internal_links, list):
                        for link in internal_links:
                            if isinstance(link, dict):
                                if 'url' in link:
                                    link_urls.append(link['url'])
                                if 'text' in link:
                                    link_texts.append(link['text'])

                    url = doc.get('url', '')
                    title = doc.get('title', '')

                    if not title and url:
                        title = extract_title_from_url(url)

                    indexed_doc = {
                        'url': url,
                        'title': title,
                        'summary': doc.get('summary', ''),
                        'content': doc.get('content', ''),
                        'categories': doc.get('categories', []),
                        'link_urls': link_urls,
                        'link_texts': link_texts
                    }

                    actions.append({
                        '_index': index_name,
                        '_id': doc_id,
                        '_source': indexed_doc
                    })
                except Exception as e:
                    print(f"Error processing document: {e}")
                    failed += 1

            if actions:
                try:
                    # Perform bulk indexing for this batch
                    success, errors = bulk(es_client, actions, refresh=True, stats_only=False)
                    successful += success

                    if errors:
                        for error in errors:
                            print(f"Indexing error: {error}")
                        failed += len(errors)
                except BulkIndexError as e:
                    print(f"Bulk indexing error: {e}")
                    print(f"First few error details: {e.errors[:3]}")
                    failed += len(e.errors)
                except Exception as e:
                    print(f"Unexpected error during batch indexing: {e}")
                    failed += len(actions)

            processed += len(batch)
            print(f"Progress: {processed}/{total_docs} documents processed, {successful} successful, {failed} failed")

    # Process documents in batches
    process_in_batches()


if __name__ == '__main__':
    main()