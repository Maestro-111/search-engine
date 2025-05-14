import scrapy
from datetime import datetime
import logging
import re


class BBCSpider(scrapy.Spider):
    name = "bbc_spider"
    allowed_domains = ["bbc.com", "bbc.co.uk"]

    # Custom settings
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 4,
        'LOG_LEVEL': 'INFO',
        'ROBOTSTXT_OBEY': False,
    }

    def __init__(self, start_urls=None, *args, **kwargs):
        super(BBCSpider, self).__init__(*args, **kwargs)
        self.start_urls = start_urls or ["https://www.bbc.com/news"]
        self.visited_urls = set()

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)


    @staticmethod
    def limit_links_per_page(links):
        return links[:300]

    def parse(self, response):

        """Parse BBC pages for links and articles."""

        self.logger.info(f"Parsing page: {response.url}")

        # Check if this is an article page
        if self.is_article_page(response.url):
            self.logger.info(f"Found article page: {response.url}")
            yield self.parse_article(response)

        # Extract all links on the page
        links = response.css('a::attr(href)').getall()
        self.logger.info(f"Found {len(links)} links on page")

        links = self.limit_links_per_page(links)

        # Process links
        for link in links:
            # Convert relative URLs to absolute URLs
            if link.startswith('/'):
                link = response.urljoin(link)

            # Only follow links within allowed domains
            if not any(domain in link for domain in self.allowed_domains):
                continue

            # Skip already visited URLs
            if link in self.visited_urls:
                continue

            # Skip non-HTTP links
            if not link.startswith('http'):
                continue

            # Add to visited list
            self.visited_urls.add(link)

            # If it's an article link, parse it as an article
            if self.is_article_page(link):
                self.logger.info(f"Following article link: {link}")
                yield scrapy.Request(url=link, callback=self.parse_article)

            # Otherwise, if it's on bbc.com/news, follow it as a regular page
            elif '/news/' in link and not any(x in link for x in ['#', 'mailto:', 'live', 'comments', 'in-pictures']):
                self.logger.info(f"Following news link: {link}")
                yield scrapy.Request(url=link, callback=self.parse)

    def is_article_page(self, url):
        """Check if a URL is likely to be a BBC article."""
        # Include both numeric IDs and alphanumeric article identifiers
        return (re.search(r'/news/.*-\d+$', url) is not None or
                re.search(r'/news/articles/[a-z0-9]+', url) is not None)

    def parse_article(self, response):

        """Extract content from a BBC article."""

        self.logger.info(f"Parsing article: {response.url}")

        # Extract title - try different selectors for BBC's layout
        title = response.css('h1::text').get()
        if not title:
            title = response.css('h1 *::text').get()
        if not title:
            title = response.css('article header h1::text').get()

        # If still no title, this might not be an article
        if not title:
            self.logger.warning(f"Could not extract title from {response.url}, might not be an article")
            return None

        self.logger.info(f"Article title: {title}")

        # Extract article ID from URL
        article_id = response.url.split('/')[-1]

        # Extract publication timestamp
        timestamp = response.css('time::attr(datetime)').get()

        # Extract author
        authors = response.css(
            'article [data-component="byline-block"] *::text, article header [data-component="byline"] *::text').getall()
        author = ' '.join([a.strip() for a in authors if a.strip()])
        if not author:
            author = response.css('div.ssrcss-68pt20-Text-TextContributorName::text').get()

        # Extract categories/tags
        category = None
        if '/news/' in response.url:
            paths = response.url.split('/news/')[1].split('/')
            if len(paths) > 0:
                category = paths[0]

        # Extract content paragraphs using multiple potential selectors
        paragraphs = []
        for selector in [
            'article [data-component="text-block"] p::text',
            'article p.ssrcss-1q0x1qg-Paragraph::text',
            'div[data-component="text-block"] p::text',
            '.article__body-content p::text'
        ]:
            p_list = response.css(selector).getall()
            if p_list:
                paragraphs.extend([p.strip() for p in p_list if p.strip()])

        content = '\n'.join(paragraphs)

        # Extract summary/description
        summary = None
        for selector in [
            'article [data-component="text-block"] p::text',
            'article .ssrcss-1q0x1qg-Paragraph::text',
            'meta[property="og:description"]::attr(content)'
        ]:
            summary_text = response.css(selector).get()
            if summary_text:
                summary = summary_text.strip()
                break

        # Extract image URLs
        image_urls = []
        for selector in [
            'article img::attr(src)',
            'div.ssrcss-11kpz0x-Placeholder img::attr(src)'
        ]:
            img_list = response.css(selector).getall()
            if img_list:
                image_urls.extend(img_list)

        # Create the item
        item = {
            'url': response.url,
            'article_id': article_id,
            'title': title,
            'author': author,
            'timestamp': timestamp,
            'category': category,
            'summary': summary,
            'content': content,
            'image_urls': image_urls,
            'crawl_time': datetime.now().isoformat()
        }

        self.logger.info(f"Extracted article with {len(paragraphs)} paragraphs")
        return item