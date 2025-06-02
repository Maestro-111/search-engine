import scrapy
from urllib.parse import urljoin, urlparse
import re


class DotabuffSpider(scrapy.Spider):

    name = "dotabuff"
    allowed_domains = ["dotabuff.com"]
    # start_urls = ['https://www.dotabuff.com/']

    # Add some headers to avoid being blocked
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 1,
        "RANDOMIZE_DOWNLOAD_DELAY": True,
        "USER_AGENT": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    def parse(self, response):
        """Parse the main page and extract initial links"""
        # Extract page content
        yield self.extract_page_data(response)

        # Find all internal links to crawl
        links = response.css("a::attr(href)").getall()

        for link in links:
            if link:
                full_url = urljoin(response.url, link)
                if self.is_valid_url(full_url):
                    yield response.follow(link, self.parse_page)

    def parse_page(self, response):
        """Parse individual pages"""
        yield self.extract_page_data(response)

        # Continue following links with depth limit
        if response.meta.get("depth", 0) < 3:  # Limit crawl depth
            links = response.css("a::attr(href)").getall()

            for link in links:
                if link:
                    full_url = urljoin(response.url, link)
                    if self.is_valid_url(full_url):
                        yield response.follow(link, self.parse_page)

    def extract_page_data(self, response):
        """Extract structured data from any page"""
        return {
            "url": response.url,
            "title": response.css("title::text").get(),
            "meta_description": response.css(
                'meta[name="description"]::attr(content)'
            ).get(),
            "h1": response.css("h1::text").getall(),
            "h2": response.css("h2::text").getall(),
            "h3": response.css("h3::text").getall(),
            "content": self.extract_text_content(response),
            "page_type": self.determine_page_type(response.url),
            "data_attributes": self.extract_data_attributes(response),
            "tables": self.extract_tables(response),
            "stats": self.extract_stats(response),
        }

    def extract_text_content(self, response):
        """Extract clean text content from the page"""
        # Remove script and style elements
        text_elements = response.css(
            "p::text, div::text, span::text, td::text, th::text"
        ).getall()

        # Clean and filter text
        clean_text = []
        for text in text_elements:
            cleaned = text.strip()
            if cleaned and len(cleaned) > 2:  # Filter out very short strings
                clean_text.append(cleaned)

        return " ".join(clean_text)

    def determine_page_type(self, url):
        """Determine what type of page this is based on URL patterns"""
        if "/players/" in url:
            return "player"
        elif "/matches/" in url:
            return "match"
        elif "/heroes/" in url:
            return "hero"
        elif "/esports/" in url:
            return "esports"
        elif "/meta/" in url:
            return "meta"
        else:
            return "general"

    def extract_data_attributes(self, response):
        """Extract data attributes that might contain structured info"""
        data_attrs = {}

        # Look for elements with data-* attributes
        elements_with_data = response.xpath('//*[@*[starts-with(name(), "data-")]]')

        for element in elements_with_data:
            attrs = element.attrib
            for key, value in attrs.items():
                if key.startswith("data-"):
                    data_attrs[key] = value

        return data_attrs

    def extract_tables(self, response):
        """Extract table data"""
        tables = []

        for table in response.css("table"):
            table_data = {"headers": table.css("th::text").getall(), "rows": []}

            for row in table.css("tr"):
                cells = row.css("td::text").getall()
                if cells:
                    table_data["rows"].append(cells)

            if table_data["headers"] or table_data["rows"]:
                tables.append(table_data)

        return tables

    def extract_stats(self, response):
        """Extract numerical stats and metrics"""
        stats = {}

        # Look for common stat patterns
        stat_elements = response.css(".stat, .number, .percentage, .value")

        for element in stat_elements:
            text = element.css("::text").get()
            if text:
                # Try to extract numbers
                numbers = re.findall(r"\d+(?:\.\d+)?%?", text.strip())
                if numbers:
                    label = (
                        element.css("::attr(title)").get()
                        or element.css("::attr(data-tooltip)").get()
                    )
                    if label:
                        stats[label] = numbers

        return stats

    def is_valid_url(self, url):
        """Check if URL should be crawled"""
        parsed = urlparse(url)

        # Only crawl dotabuff.com
        if parsed.netloc != "www.dotabuff.com" and parsed.netloc != "dotabuff.com":
            return False

        # Skip certain file types
        skip_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".pdf",
            ".zip",
            ".css",
            ".js",
        ]
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        # Skip certain paths that might not be useful
        skip_paths = ["/api/", "/ajax/", "/assets/"]
        if any(skip_path in url for skip_path in skip_paths):
            return False

        return True
