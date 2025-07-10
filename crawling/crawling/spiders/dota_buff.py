import scrapy
import re
from datetime import datetime


class DotabuffMatchSpider(scrapy.Spider):

    name = "dotabuff_matches"
    allowed_domains = ["dotabuff.com"]

    # Start with recent matches and hero pages
    start_urls = [
        "https://www.dotabuff.com/matches",
        "https://www.dotabuff.com/heroes",
        "https://www.dotabuff.com/heroes/meta",
        "https://www.dotabuff.com/heroes/winning",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "crawling.pipelines.DotabuffMongoPipeline": 100,
        "DEPTH_LIMIT": 5,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matches_crawled = 0
        self.max_matches = 10000  # Limit for initial crawl

    def parse(self, response):
        """Route to appropriate parser based on URL"""
        if "/matches" in response.url and "/matches/" not in response.url:
            yield from self.parse_matches_list(response)
        elif "/heroes" in response.url and "/heroes/" not in response.url:
            yield from self.parse_heroes_list(response)
        elif "/matches/" in response.url:
            yield from self.parse_match_detail(response)
        elif "/heroes/" in response.url:
            yield from self.parse_hero_detail(response)

    def parse_matches_list(self, response):
        """Parse matches list page"""
        # Extract match links
        match_links = response.css('a[href*="/matches/"]::attr(href)').getall()

        for link in match_links[:50]:  # Limit per page
            if self.matches_crawled < self.max_matches:
                self.matches_crawled += 1
                yield response.follow(link, self.parse_match_detail)

        # Follow pagination
        next_page = response.css("a.next::attr(href)").get()
        if next_page and self.matches_crawled < self.max_matches:
            yield response.follow(next_page, self.parse_matches_list)

    def parse_heroes_list(self, response):
        """Parse heroes list page"""
        hero_links = response.css('a[href*="/heroes/"]::attr(href)').getall()

        for link in hero_links:
            if re.match(r"/heroes/[a-z-]+$", link):  # Only hero detail pages
                yield response.follow(link, self.parse_hero_detail)

    def parse_match_detail(self, response):
        """Extract detailed match data"""
        match_id = self.extract_match_id(response.url)

        match_data = {
            "type": "match",
            "match_id": match_id,
            "url": response.url,
            "timestamp": datetime.utcnow().isoformat(),
            # Match info
            "duration": self.extract_duration(response),
            "game_mode": response.css(".game-mode::text").get(),
            "skill_bracket": response.css(".skill-bracket::text").get(),
            "region": response.css(".region::text").get(),
            "patch": response.css(".patch::text").get(),
            # Teams
            "radiant": self.extract_team_data(response, "radiant"),
            "dire": self.extract_team_data(response, "dire"),
            # Result
            "winner": self.extract_winner(response),
            # Additional stats
            "first_blood_time": self.extract_stat(response, "first-blood"),
            "total_kills": self.extract_total_kills(response),
        }

        yield match_data

    def parse_hero_detail(self, response):
        """Extract hero statistics and matchup data"""
        hero_name = self.extract_hero_name(response.url)

        hero_data = {
            "type": "hero",
            "hero_name": hero_name,
            "url": response.url,
            "timestamp": datetime.utcnow().isoformat(),
            # General stats
            "win_rate": self.extract_percentage(response, "win-rate"),
            "pick_rate": self.extract_percentage(response, "pick-rate"),
            "ban_rate": self.extract_percentage(response, "ban-rate"),
            # Role info
            "roles": response.css(".hero-roles span::text").getall(),
            "lane_presence": self.extract_lane_presence(response),
            # Matchups
            "best_versus": self.extract_matchups(response, "best-versus"),
            "worst_versus": self.extract_matchups(response, "worst-versus"),
            # Item builds
            "popular_items": self.extract_items(response, "popular"),
            "winning_items": self.extract_items(response, "winning"),
            # Ability builds
            "ability_builds": self.extract_ability_builds(response),
            # Stats by skill bracket
            "stats_by_bracket": self.extract_stats_by_bracket(response),
        }

        yield hero_data

        # Follow matchup links for more detailed data
        matchup_links = response.css(
            'a[href*="/heroes/"][href*="/matchups"]::attr(href)'
        ).getall()
        for link in matchup_links[:5]:  # Limit to avoid too many requests
            yield response.follow(link, self.parse_hero_matchups)

    def parse_hero_matchups(self, response):
        """Parse detailed hero matchup page"""
        hero_name = self.extract_hero_name(response.url)

        matchup_data = {
            "type": "hero_matchups",
            "hero_name": hero_name,
            "url": response.url,
            "timestamp": datetime.utcnow().isoformat(),
            "matchups": [],
        }

        # Extract all matchup rows
        for row in response.css("table.matchups tr"):
            opponent = row.css("td.cell-xlarge a::text").get()
            if opponent:
                matchup_data["matchups"].append(
                    {
                        "opponent": opponent,
                        "advantage": row.css("td[data-value]::attr(data-value)").get(),
                        "win_rate": row.css("td:nth-child(3)::text").get(),
                        "matches_played": row.css("td:nth-child(4)::text").get(),
                    }
                )

        yield matchup_data

    def extract_team_data(self, response, team):
        """Extract data for one team (radiant/dire)"""
        team_selector = f".team-{team}"

        players = []
        for player_row in response.css(f"{team_selector} tbody tr"):
            player_data = {
                "hero": player_row.css("td.cell-xlarge a::text").get(),
                "player_name": player_row.css("td.tf-pl a::text").get(),
                "level": player_row.css("td.r-tab::text").get(),
                "kills": player_row.css("td.r-tab:nth-child(3)::text").get(),
                "deaths": player_row.css("td.r-tab:nth-child(4)::text").get(),
                "assists": player_row.css("td.r-tab:nth-child(5)::text").get(),
                "gold": player_row.css("td.r-tab:nth-child(6)::text").get(),
                "last_hits": player_row.css("td.r-tab:nth-child(7)::text").get(),
                "denies": player_row.css("td.r-tab:nth-child(8)::text").get(),
                "gpm": player_row.css("td.r-tab:nth-child(9)::text").get(),
                "xpm": player_row.css("td.r-tab:nth-child(10)::text").get(),
                "items": self.extract_player_items(player_row),
            }
            players.append(player_data)

        return {
            "players": players,
            "total_kills": response.css(
                f"{team_selector} .team-results span.kills::text"
            ).get(),
            "total_gold": response.css(
                f"{team_selector} .team-results span.gold::text"
            ).get(),
            "total_xp": response.css(
                f"{team_selector} .team-results span.xp::text"
            ).get(),
        }

    def extract_player_items(self, player_row):
        """Extract items for a player"""
        items = []
        for item in player_row.css(".items img"):
            item_name = item.css("::attr(alt)").get()
            if item_name:
                items.append(item_name)
        return items

    def extract_matchups(self, response, matchup_type):
        """Extract hero matchup data"""
        matchups = []
        selector = f".{matchup_type} tr"

        for row in response.css(selector)[:10]:  # Top 10
            hero = row.css("td.cell-xlarge a::text").get()
            advantage = row.css("td[data-value]::attr(data-value)").get()
            if hero and advantage:
                matchups.append(
                    {"hero": hero, "advantage": float(advantage) if advantage else 0}
                )

        return matchups

    def extract_items(self, response, item_type):
        """Extract item build data"""
        items = []
        selector = f".{item_type}-items .item"

        for item in response.css(selector):
            item_name = item.css("img::attr(alt)").get()
            usage_rate = item.css(".usage::text").get()
            if item_name:
                items.append({"name": item_name, "usage_rate": usage_rate})

        return items

    def extract_ability_builds(self, response):
        """Extract ability build orders"""
        builds = []

        for build in response.css(".ability-build"):
            build_data = {
                "usage_rate": build.css(".usage::text").get(),
                "win_rate": build.css(".win-rate::text").get(),
                "build_order": build.css(".ability::attr(alt)").getall(),
            }
            builds.append(build_data)

        return builds

    def extract_stats_by_bracket(self, response):
        """Extract statistics by skill bracket"""
        stats = {}

        for row in response.css(".bracket-stats tr"):
            bracket = row.css("td:first-child::text").get()
            if bracket:
                stats[bracket] = {
                    "pick_rate": row.css("td:nth-child(2)::text").get(),
                    "win_rate": row.css("td:nth-child(3)::text").get(),
                    "kda": row.css("td:nth-child(4)::text").get(),
                }

        return stats

    def extract_lane_presence(self, response):
        """Extract lane presence data"""
        lanes = {}

        for lane in ["safe", "mid", "off", "jungle", "roaming"]:
            presence = response.css(f".lane-{lane} .presence::text").get()
            if presence:
                lanes[lane] = presence

        return lanes

    # Utility methods
    def extract_match_id(self, url):
        """Extract match ID from URL"""
        match = re.search(r"/matches/(\d+)", url)
        return match.group(1) if match else None

    def extract_hero_name(self, url):
        """Extract hero name from URL"""
        match = re.search(r"/heroes/([a-z-]+)", url)
        return match.group(1) if match else None

    def extract_duration(self, response):
        """Extract match duration"""
        duration = response.css(".duration::text").get()
        if duration:
            # Convert MM:SS to seconds
            parts = duration.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        return None

    def extract_winner(self, response):
        """Determine match winner"""
        radiant_win = response.css(".radiant.winner").get()
        if radiant_win:
            return "radiant"
        dire_win = response.css(".dire.winner").get()
        if dire_win:
            return "dire"
        return None

    def extract_percentage(self, response, stat_type):
        """Extract percentage values"""
        value = response.css(f".{stat_type}::text").re_first(r"([\d.]+)%")
        return float(value) if value else None

    def extract_stat(self, response, stat_name):
        """Extract generic stat value"""
        return response.css(f".{stat_name}::text").get()

    def extract_total_kills(self, response):
        """Extract total kills in match"""
        radiant_kills = response.css(".radiant .kills::text").get()
        dire_kills = response.css(".dire .kills::text").get()

        if radiant_kills and dire_kills:
            return int(radiant_kills) + int(dire_kills)
        return None
