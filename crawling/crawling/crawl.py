# search-engine/crawling/crawl.py
import argparse
import os
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.wikipedia import WikipediaSpider
from spiders.reddit import RedditSpider
from spiders.bbc import BBCSpider

# from spiders.dota_buff import DotabuffMatchSpider
from spiders.dota_api import OpenDotaCollector


class SpiderNotImplenetedException(Exception):
    pass


def main():

    parser = argparse.ArgumentParser(description="Start a web crawling job")

    parser.add_argument(
        "--seed-url",
        type=str,
        default="",
        help="Starting URL for the crawler",
    )
    parser.add_argument(
        "--mongo-uri",
        type=str,
        default=os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
        help="MongoDB connection URI",
    )
    parser.add_argument(
        "--mongo-db", type=str, default="wikipedia_db", help="MongoDB database name"
    )
    parser.add_argument(
        "--mongo-collection",
        type=str,
        default="articles",
        help="MongoDB collection name",
    )
    parser.add_argument(
        "--depth-limit",
        type=int,
        default=1,
        help="Maximum depth for crawler to follow links",
    )
    parser.add_argument(
        "--page-limit", type=int, default=5, help="Maximum number of pages to crawl"
    )
    parser.add_argument(
        "--spider-name", type=str, default="wikipedia_spider", help="Name of the spider"
    )

    args = parser.parse_args()

    # Configure settings
    settings = get_project_settings()

    settings.set("ITEM_PIPELINES", {"crawling.pipelines.MongoDBPipeline": 100})
    settings.set("MONGODB_URI", args.mongo_uri)
    settings.set("MONGODB_DATABASE", args.mongo_db)
    settings.set("MONGODB_COLLECTION", args.mongo_collection)
    settings.set("DEPTH_LIMIT", args.depth_limit)
    settings.set("CLOSESPIDER_PAGECOUNT", args.page_limit)

    print("MONGODB settings:")

    print("ITEM_PIPELINES:", settings["ITEM_PIPELINES"])
    print("depth", settings.get("DEPTH_LIMIT"))
    print("count pages", settings.get("CLOSESPIDER_PAGECOUNT"))
    print("URI:", settings.get("MONGODB_URI"))
    print("DB:", settings.get("MONGODB_DATABASE"))
    print("COLLECTION:", settings.get("MONGODB_COLLECTION"))
    print("ITEM_PIPELINES:", settings.get("ITEM_PIPELINES"))

    try:

        mongodb_uri = settings.get("MONGODB_URI")
        mongodb_db = settings.get("MONGODB_DATABASE")
        mongodb_collection = settings.get("MONGODB_COLLECTION")

        print(f"Connecting to: {mongodb_uri}")
        print(f"Using database: {mongodb_db}")
        print(f"Using collection: {mongodb_collection}")

    except Exception as e:
        print("MongoDB Error:", e)
    else:
        print("MongoDB connection successful")

    if args.spider_name == "wikipedia_spider":
        process = CrawlerProcess(settings)
        process.crawl(WikipediaSpider, start_urls=[args.seed_url])
        process.start()
    elif args.spider_name == "reddit_spider":
        process = CrawlerProcess(settings)
        process.crawl(RedditSpider, start_urls=[args.seed_url])
        process.start()
    elif args.spider_name == "bbc_spider":
        process = CrawlerProcess(settings)
        process.crawl(BBCSpider, start_urls=[args.seed_url])
        process.start()
    elif args.spider_name == "dota_spider":

        collector = OpenDotaCollector(
            mongo_uri=args.mongo_uri,
            db_name=args.mongo_db,
            collection_name=args.mongo_collection,
        )

        collector.collect_hero_data()
        collector.collect_matches()

        stats = collector.get_match_statistics()
        hero_winrates = collector.get_hero_winrates()

        print(f"Match statistics: {stats}")

        print("Top 5 heroes by winrate:")
        for hero in hero_winrates[:5]:
            print(
                f"Hero {hero['hero_id']}: {hero['winrate']:.2%} ({hero['matches']} matches)"
            )

    else:
        raise SpiderNotImplenetedException(
            "Spider name '{}' not implemented".format(args.spider_name)
        )


if __name__ == "__main__":
    main()
