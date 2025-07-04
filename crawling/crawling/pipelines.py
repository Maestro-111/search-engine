import pymongo
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter


class MongoDBPipeline:

    def __init__(self, mongo_uri, mongo_db, collection_name):

        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.collection_name = collection_name
        self.client = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get("MONGODB_URI", "mongodb://localhost:27017"),
            mongo_db=crawler.settings.get("MONGODB_DATABASE", "wikipedia_db"),
            collection_name=crawler.settings.get("MONGODB_COLLECTION", "articles"),
        )

    def open_spider(self, spider):

        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        self.db[self.collection_name].create_index("url", unique=True)

    def close_spider(self, spider):
        self.client.close()  # type: ignore

    def process_item(self, item, spider):

        adapter = ItemAdapter(item)

        print(f"MongoDBPipeline.process_item: Processing {adapter['url']}")

        try:

            self.db[self.collection_name].update_one(  # type: ignore
                {"url": adapter["url"]},  # Query for finding the document
                {"$set": dict(adapter)},  # Update with new data
                upsert=True,  # Insert if not exists
            )

        except pymongo.errors.DuplicateKeyError:
            raise DropItem(f"Duplicate item found: {item['url']}")

        print("Item successfully processed by MongoDB pipeline")
        return item
