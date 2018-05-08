import scrapy
import datetime

from scrapy.spiders import CrawlSpider

#Import de la class Item Article.
from micorr_crawlers.items.Article import Article

# AWS API services
import botocore.session

class epsc_Spider(CrawlSpider):

	# epreservation science
	# http://www.morana-rtd.com/e-preservationscience/TOC.html
	name = "epsc"
	allowed_domains = ['www.morana-rtd.com/e-preservationscience/TOC.html']

	# Boto3 session for S3.
	session = botocore.session.get_session()
	client = session.create_client('s3', region_name='eu-central-1')

	# Liste des volumes
	start_urls = ['http://www.morana-rtd.com/e-preservationscience/TOC.html']
	# Url de base utilisée pour les requêtes de navigation.
	BASE_URL = 'http://www.morana-rtd.com'

	def parse(self, response):
		raise CloseSpider('Not Implemented yet.')

		# Create article
		article = Article()

		# For all article on a page.
		for a in response.css('tbody tr td p'):

			# Extract metadata.
			article['file_urls'] = a.css('a[href$=".pdf"]::attr(href)').extract()

			yield article

		return article
