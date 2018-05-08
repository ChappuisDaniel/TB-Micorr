import scrapy
import datetime

from scrapy.spiders import CrawlSpider

#Import de la class Item Article.
from micorr_crawlers.items.Article import Article

# AWS API services
import botocore.session

class coch_Spider(CrawlSpider):

	# Conservation science in Cultural Heritage
	# https://conservation-science.unibo.it/
	name = "coch"
	allowed_domains = ['www.conservation-science.unibo.it']

	# Boto3 session for S3.
	session = botocore.session.get_session()
	client = session.create_client('s3', region_name='eu-central-1')

	# Liste des volumes
	start_urls = ['https://conservation-science.unibo.it/issue/view/691/showToc']
	# Url de base utilisée pour les requêtes de navigation.
	BASE_URL = 'https://conservation-science.unibo.it'

	def parse(self, response):
		raise CloseSpider('Not Implemented yet.')

		# Open volume
		for volume in response.css('table.tocArticle'):

			articleLink = volume.css('div.tocGalleys a.file::attr(href)').extract_first()

			# Extract metadata.
			yield {
				'title': volume.css('div.tocTitle a::text').extract(),
				'author': volume.css('div.tocAuthors::text').extract(),
				'link': articleLink
			}

			# Should download PDF.
			yield scrapy.Request(url=articleLink, callback=self.parse_article)
