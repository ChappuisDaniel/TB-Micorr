import scrapy

class Article(scrapy.Item):
    title = scrapy.Field()
    authors = scrapy.Field()
    abstract = scrapy.Field()
    releaseDate = scrapy.Field()
    articleType = scrapy.Field()
    fullText = scrapy.Field()
    fileURL = scrapy.Field()
    lastUpdate = scrapy.Field()
    topics = scrapy.Field()
