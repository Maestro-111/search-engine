import pymongo
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
from datetime import datetime
import logging


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


class DotabuffMongoPipeline:
    """Pipeline to store Dotabuff data in MongoDB with proper structure"""

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.logger = logging.getLogger(__name__)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.getlist("MONGODB_URI")[0],
            mongo_db=crawler.settings.get("MONGODB_DATABASE", "dotabuff"),
        )

    def open_spider(self, spider):
        """Initialize MongoDB connection"""
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

        # Create indexes for better query performance
        self.create_indexes()

    def close_spider(self, spider):
        """Close MongoDB connection"""
        self.client.close()

    def create_indexes(self):
        """Create indexes for efficient querying"""
        # Matches collection indexes
        self.db.matches.create_index("match_id", unique=True)
        self.db.matches.create_index("timestamp")
        self.db.matches.create_index("winner")
        self.db.matches.create_index("skill_bracket")
        self.db.matches.create_index(
            [("radiant.players.hero", 1), ("dire.players.hero", 1)]
        )

        # Heroes collection indexes
        self.db.heroes.create_index("hero_name", unique=True)
        self.db.heroes.create_index("win_rate")
        self.db.heroes.create_index("pick_rate")

        # Hero matchups collection indexes
        self.db.hero_matchups.create_index([("hero_name", 1), ("timestamp", -1)])

        self.logger.info("MongoDB indexes created")

    def process_item(self, item, spider):
        """Process and store items based on their type"""
        item_type = item.get("type")

        if item_type == "match":
            self.process_match(item)
        elif item_type == "hero":
            self.process_hero(item)
        elif item_type == "hero_matchups":
            self.process_hero_matchups(item)

        return item

    def process_match(self, item):
        """Process and store match data"""
        # Clean and transform match data
        match_data = {
            "match_id": item["match_id"],
            "url": item["url"],
            "crawled_at": datetime.utcnow(),
            "duration": item.get("duration"),
            "game_mode": item.get("game_mode"),
            "skill_bracket": item.get("skill_bracket"),
            "region": item.get("region"),
            "patch": item.get("patch"),
            "winner": item.get("winner"),
            "first_blood_time": item.get("first_blood_time"),
            "total_kills": item.get("total_kills"),
            # Team compositions
            "radiant_heroes": [
                p["hero"] for p in item["radiant"]["players"] if p.get("hero")
            ],
            "dire_heroes": [
                p["hero"] for p in item["dire"]["players"] if p.get("hero")
            ],
            # Full team data
            "radiant": item["radiant"],
            "dire": item["dire"],
            # Calculated fields for analysis
            "hero_matchups": self.calculate_hero_matchups(item),
            "team_compositions": {
                "radiant": self.analyze_team_composition(item["radiant"]["players"]),
                "dire": self.analyze_team_composition(item["dire"]["players"]),
            },
        }

        # Upsert match data
        self.db.matches.update_one(
            {"match_id": match_data["match_id"]}, {"$set": match_data}, upsert=True
        )

        # Update match statistics collection
        self.update_match_statistics(match_data)

    def process_hero(self, item):
        """Process and store hero data"""
        hero_data = {
            "hero_name": item["hero_name"],
            "url": item["url"],
            "last_updated": datetime.utcnow(),
            "stats": {
                "win_rate": item.get("win_rate"),
                "pick_rate": item.get("pick_rate"),
                "ban_rate": item.get("ban_rate"),
            },
            "roles": item.get("roles", []),
            "lane_presence": item.get("lane_presence", {}),
            "best_versus": item.get("best_versus", []),
            "worst_versus": item.get("worst_versus", []),
            "popular_items": item.get("popular_items", []),
            "winning_items": item.get("winning_items", []),
            "ability_builds": item.get("ability_builds", []),
            "stats_by_bracket": item.get("stats_by_bracket", {}),
        }

        # Upsert hero data
        self.db.heroes.update_one(
            {"hero_name": hero_data["hero_name"]}, {"$set": hero_data}, upsert=True
        )

    def process_hero_matchups(self, item):
        """Process and store detailed hero matchup data"""
        matchup_data = {
            "hero_name": item["hero_name"],
            "url": item["url"],
            "timestamp": datetime.utcnow(),
            "matchups": item.get("matchups", []),
        }

        # Store in separate collection for historical tracking
        self.db.hero_matchups.insert_one(matchup_data)

        # Also update the main heroes collection with latest matchup data
        self.db.heroes.update_one(
            {"hero_name": item["hero_name"]},
            {
                "$set": {
                    "detailed_matchups": item.get("matchups", []),
                    "matchups_updated": datetime.utcnow(),
                }
            },
        )

    def calculate_hero_matchups(self, match_item):
        """Calculate hero matchup pairs from a match"""
        matchups = []
        radiant_heroes = [
            p["hero"] for p in match_item["radiant"]["players"] if p.get("hero")
        ]
        dire_heroes = [
            p["hero"] for p in match_item["dire"]["players"] if p.get("hero")
        ]

        # Create matchup pairs
        for r_hero in radiant_heroes:
            for d_hero in dire_heroes:
                matchups.append(
                    {
                        "hero1": r_hero,
                        "hero2": d_hero,
                        "hero1_team": "radiant",
                        "hero2_team": "dire",
                        "hero1_won": match_item.get("winner") == "radiant",
                    }
                )

        return matchups

    def analyze_team_composition(self, players):
        """Analyze team composition for roles and synergy"""
        composition = {
            "carry_count": 0,
            "support_count": 0,
            "initiator_count": 0,
            "nuker_count": 0,
            "disabler_count": 0,
            "durable_count": 0,
            "pusher_count": 0,
            "heroes": [p["hero"] for p in players if p.get("hero")],
        }

        # This would be enhanced with actual hero role data
        # For now, returning basic structure
        return composition

    def update_match_statistics(self, match_data):
        """Update aggregated statistics collection"""
        stats_update = {"total_matches": 1, "last_updated": datetime.utcnow()}

        # Update win counters
        if match_data.get("winner"):
            stats_update[f"{match_data['winner']}_wins"] = 1

        # Update hero pick statistics
        all_heroes = match_data["radiant_heroes"] + match_data["dire_heroes"]
        for hero in all_heroes:
            self.db.hero_stats.update_one(
                {"hero_name": hero},
                {
                    "$inc": {
                        "picks": 1,
                        "wins": (
                            1
                            if (
                                (
                                    hero in match_data["radiant_heroes"]
                                    and match_data["winner"] == "radiant"
                                )
                                or (
                                    hero in match_data["dire_heroes"]
                                    and match_data["winner"] == "dire"
                                )
                            )
                            else 0
                        ),
                    },
                    "$set": {"last_seen": datetime.utcnow()},
                },
                upsert=True,
            )

        # Update global statistics
        self.db.statistics.update_one(
            {"_id": "global"}, {"$inc": stats_update}, upsert=True
        )
