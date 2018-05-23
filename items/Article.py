import scrapy

class Article(scrapy.Item):
    id = scrapy.Field()
    type = scrapy.Field()
    fields = scrapy.Field()
    
class Fields(scrapy.Item):
    title = scrapy.Field()
    authors = scrapy.Field()
    abstract = scrapy.Field()
    release_date = scrapy.Field()
    article_type = scrapy.Field()
    fulltext = scrapy.Field()
    file_url = scrapy.Field()
    keywords = scrapy.Field()
    topics = scrapy.Field()
    last_update = scrapy.Field()
