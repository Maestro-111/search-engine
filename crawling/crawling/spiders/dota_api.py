import requests  # type: ignore
import pymongo
from datetime import datetime
import time
import logging


class OpenDotaCollector:
    """Collect Dota 2 match and hero data from OpenDota API"""

    def __init__(
        self, mongo_uri, db_name="dota_db", collection_name="match_simulator_db"
    ):
        self.api_base = "https://api.opendota.com/api"
        self.mongo_client = pymongo.MongoClient(mongo_uri)
        self.db = self.mongo_client[db_name]
        self.collection = self.db[collection_name]
        self.logger = logging.getLogger(__name__)

        # Create indexes
        self.collection.create_index("match_id", unique=True)
        self.collection.create_index("radiant_team")
        self.collection.create_index("dire_team")
        self.collection.create_index("start_time")

        logging.basicConfig(level=logging.INFO)

    def get_recent_matches(self, limit=100):
        """Get recent public matches"""
        url = f"{self.api_base}/publicMatches"
        response = requests.get(url)
        if response.status_code == 200:
            matches = response.json()
            return matches[:limit]
        return []

    def get_match_details(self, match_id):
        """Get detailed match information"""
        url = f"{self.api_base}/matches/{match_id}"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None

    def get_heroes(self):
        """Get all hero data"""
        url = f"{self.api_base}/heroes"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    def get_hero_stats(self):
        """Get hero statistics"""
        url = f"{self.api_base}/heroStats"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return []

    def process_match(self, match_data):
        """Process and store match data"""
        if not match_data:
            return

        # Extract team compositions
        radiant_team = []
        dire_team = []

        for player in match_data.get("players", []):
            hero_id = player.get("hero_id")
            if hero_id:
                if player.get("player_slot", 0) < 128:  # Radiant
                    radiant_team.append(hero_id)
                else:  # Dire
                    dire_team.append(hero_id)

        # Prepare match document
        match_doc = {
            "match_id": match_data["match_id"],
            "start_time": match_data.get("start_time"),
            "duration": match_data.get("duration"),
            "radiant_win": match_data.get("radiant_win"),
            "radiant_team": radiant_team,
            "dire_team": dire_team,
            "game_mode": match_data.get("game_mode"),
            "lobby_type": match_data.get("lobby_type"),
            "skill": match_data.get("skill"),
            "radiant_score": match_data.get("radiant_score"),
            "dire_score": match_data.get("dire_score"),
            "players": match_data.get("players", []),
            "patch": match_data.get("patch"),
            "region": match_data.get("region"),
            "crawled_at": datetime.utcnow(),
        }

        # Upsert to MongoDB
        self.collection.update_one(
            {"match_id": match_doc["match_id"]}, {"$set": match_doc}, upsert=True
        )
        self.logger.info(f"Processed match {match_doc['match_id']}")

    def collect_matches(self, num_matches=1000, delay=1):
        """Collect a specified number of matches"""
        self.logger.info(f"Starting to collect {num_matches} matches...")

        # Get recent matches
        recent_matches = self.get_recent_matches(min(num_matches, 100))

        collected = 0
        for match in recent_matches:
            match_id = match["match_id"]

            # Get detailed match data
            match_details = self.get_match_details(match_id)
            if match_details:
                self.process_match(match_details)
                collected += 1

                if collected >= num_matches:
                    break

                # Rate limiting
                time.sleep(delay)

        self.logger.info(f"Collected {collected} matches")

    def collect_hero_data(self):
        """Collect and store hero data"""
        self.logger.info("Collecting hero data...")

        # Get basic hero info
        heroes = self.get_heroes()
        hero_stats = self.get_hero_stats()

        # Create hero collection
        hero_collection = self.db["heroes"]
        hero_collection.create_index("id", unique=True)

        # Merge hero data with stats
        hero_dict = {h["id"]: h for h in heroes}

        for stat in hero_stats:
            hero_id = stat["id"]
            if hero_id in hero_dict:
                hero_doc = {
                    **hero_dict[hero_id],
                    **stat,
                    "updated_at": datetime.utcnow(),
                }

                hero_collection.update_one(
                    {"id": hero_id}, {"$set": hero_doc}, upsert=True
                )

        self.logger.info(f"Collected data for {len(heroes)} heroes")

    def get_match_statistics(self):
        """Calculate match statistics for prediction model"""
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_matches": {"$sum": 1},
                    "radiant_wins": {"$sum": {"$cond": ["$radiant_win", 1, 0]}},
                    "avg_duration": {"$avg": "$duration"},
                }
            }
        ]

        stats = list(self.collection.aggregate(pipeline))
        return stats[0] if stats else {}

    def get_hero_winrates(self):
        """Calculate hero win rates from collected matches"""
        pipeline = [
            {"$project": {"players": 1, "radiant_win": 1}},
            {"$unwind": "$players"},
            {
                "$project": {
                    "hero_id": "$players.hero_id",
                    "is_radiant": {"$lt": ["$players.player_slot", 128]},
                    "radiant_win": 1,
                }
            },
            {
                "$project": {
                    "hero_id": 1,
                    "won": {
                        "$or": [
                            {"$and": ["$is_radiant", "$radiant_win"]},
                            {
                                "$and": [
                                    {"$not": "$is_radiant"},
                                    {"$not": "$radiant_win"},
                                ]
                            },
                        ]
                    },
                }
            },
            {
                "$group": {
                    "_id": "$hero_id",
                    "matches": {"$sum": 1},
                    "wins": {"$sum": {"$cond": ["$won", 1, 0]}},
                }
            },
            {
                "$project": {
                    "hero_id": "$_id",
                    "matches": 1,
                    "wins": 1,
                    "winrate": {"$divide": ["$wins", "$matches"]},
                }
            },
            {"$sort": {"winrate": -1}},
        ]

        return list(self.collection.aggregate(pipeline))
