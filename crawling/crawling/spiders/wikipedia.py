import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import re
from datetime import datetime


class WikipediaSpider(CrawlSpider):

    name = "wikipedia"
    allowed_domains = ["en.wikipedia.org"]

    # Rules for link extraction and following
    rules = (
        # Follow wiki article links
        Rule(
            LinkExtractor(
                allow=r'/wiki/[^:]+$',  # Match wiki article URLs, exclude special pages that contain ":"
                deny=(r'/wiki/Wikipedia:', r'/wiki/Help:', r'/wiki/File:', r'/wiki/Portal:')
            ),
            callback='parse_article',
            follow=True,
            process_links='limit_links_per_page'
        ),
    )

    def __init__(self, *args, **kwargs):

        self.start_urls = kwargs.pop('start_urls', ["https://en.wikipedia.org/wiki/World_War_II"])
        super(WikipediaSpider, self).__init__(*args, **kwargs)

    def limit_links_per_page(self, links):
        return links[:300]

    def parse_article(self, response):
        """Extract content from a Wikipedia article."""

        title = response.css('h1#firstHeading::text').get()
        content_paragraphs = response.css('div.mw-parser-output p')

        # First join the text fragments within each paragraph, then join paragraphs

        content = '\n'.join([' '.join(p.css('::text').getall()) for p in content_paragraphs])
        content = self.clean_text(content)

        # Extract categories
        categories = response.css('div.mw-normal-catlinks ul li a::text').getall()

        # Extract infobox data if present (structured data from the right-side box)
        infobox_data = {}
        infobox_rows = response.css('table.infobox tr')
        for row in infobox_rows:
            header = row.css('th ::text').get()
            value = ' '.join(row.css('td ::text').getall())
            if header and value:
                infobox_data[self.clean_text(header)] = self.clean_text(value)

        # Extract summary (first paragraph of content)
        summary = ""
        for p in content_paragraphs:
            text = p.css('::text').getall()
            if text and ''.join(text).strip():
                summary = self.clean_text(' '.join(text))
                break

        # Extract links to other Wikipedia articles
        internal_links = []
        for link in response.css('div.mw-parser-output p a[href^="/wiki/"]'):
            href = link.css('::attr(href)').get()
            text = link.css('::text').get()
            if href and text and not any(x in href for x in [':', 'redlink']):
                internal_links.append({
                    'url': response.urljoin(href),
                    'text': text.strip()
                })

        # Extract last modified date
        last_modified = response.css('#footer-info-lastmod::text').get()
        if last_modified:
            # Try to extract the date using regex
            date_match = re.search(r'(\d+ [A-Z][a-z]+ \d+)', last_modified)
            if date_match:
                last_modified = date_match.group(1)
            else:
                last_modified = None

        print({
            'url': response.url,
            'title': title,
            'summary': summary,
            'content': content,
            'categories': categories,
            'infobox': infobox_data,
            'internal_links': internal_links,
            'last_modified': last_modified,
            'crawl_time': datetime.now().isoformat()
        }
)

        yield {
            'url': response.url,
            'title': title,
            'summary': summary,
            'content': content,
            'categories': categories,
            'infobox': infobox_data,
            'internal_links': internal_links,
            'last_modified': last_modified,
            'crawl_time': datetime.now().isoformat()
        }

    def clean_text(self, text):

        """Clean up extracted text by removing extra whitespace and citations."""

        if not text:
            return ""

        # If text is a list, join it
        if isinstance(text, list):
            text = ' '.join(text)

        # Remove citations [1], [2], etc.
        text = re.sub(r'\[\d+\]', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text