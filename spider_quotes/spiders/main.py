from twisted.internet import reactor, defer
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
import scrapy
from scrapy.crawler import CrawlerProcess, CrawlerRunner

author_links = []


def store_urls(url: str):
    if url not in author_links:
        author_links.append(url)


class MainSpider(scrapy.Spider):
    name = "main"
    custom_settings = {"FEED_FORMAT": "json", "FEED_URI": "quotes.json"}
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com"]

    def parse(self, response):
        quotes = response.xpath("/html//div[@class='quote']")
        for quote in quotes:
            author = quote.xpath("span/small/text()").get()
            store_urls(self.start_urls[0] + quote.xpath("span/a/@href").get() + "/")
            # author_links[author] = (
            #     self.start_urls[0] + quote.xpath("span/a/@href").get() + "/"
            # )

            yield {
                "tags": quote.xpath("div[@class='tags']/a/text()").getall(),
                "author": author,
                "quote": quote.xpath("span[@class='text']/text()")
                .get()
                .replace("“", "")
                .replace("”", ""),
            }
        next_link = response.xpath("//li[@class='next']/a/@href").get()
        if next_link:
            yield scrapy.Request(url=self.start_urls[0] + next_link)


class AuthorSpider(scrapy.Spider):
    name = "author"
    custom_settings = {"FEED_FORMAT": "json", "FEED_URI": "authors.json"}
    allowed_domains = ["quotes.toscrape.com"]

    def start_requests(self):
        for url in author_links:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        name = response.xpath("/html//h3[@class='author-title']/text()").get()
        yield {
            "fullname": name,
            "born-date": response.xpath(
                "/html//span[@class='author-born-date']/text()"
            ).get(),
            "born-locate": response.xpath(
                "/html//span[@class='author-born-location']/text()"
            ).get(),
            "description": response.xpath(
                "/html//div[@class='author-description']/text()"
            ).get(),
        }


runner = CrawlerRunner()


@defer.inlineCallbacks
def crawl():
    yield runner.crawl(MainSpider)
    yield runner.crawl(AuthorSpider)
    reactor.stop()


crawl()
reactor.run()
# process = CrawlerProcess()
# process.crawl(MainSpider)
# process.crawl(AuthorSpider)
# process.start()
