import scrapy
import datetime

from scrapy.spiders import CrawlSpider

#Import de la class Item Article.
from micorr_crawlers.items.Article import Article

# AWS API services
import botocore.session

class ecjo_Spider(CrawlSpider):

	# e-conservation Journal
	# http://e-conservation.org/
	name = "ecjo"
	allowed_domains = ['www.sciencedirect.com/journal/journal-of-cultural-heritage']

	# Boto3 session for S3.
	session = botocore.session.get_session()
	client = session.create_client('s3', region_name='eu-central-1')

	# Liste des articles.
	start_urls = ['http://e-conservation.org/journal']
	# Url de base utilisée pour les requêtes de navigation.
	BASE_URL = 'http://e-conservation.org/'

	def parse(self, response):
		raise CloseSpider('Not Implemented yet.')
