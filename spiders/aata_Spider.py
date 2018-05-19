import os, json, io, datetime
from RISparser import readris

import scrapy
from scrapy.spiders import CrawlSpider

from bs4 import BeautifulSoup

# Import de la class Item Article.
from micorr_crawlers.items.Article import Article

# AWS API services
import botocore.session
import boto3

class aata_Spider(CrawlSpider):

	# AATA
	# http://aata.getty.edu
	name = "aata"
	allowed_domains = ['aata.getty.edu']

	# Boto3 session for S3.
	session = botocore.session.get_session()
	# Has to be in us-east where CloudSearch is avilable.
	client = session.create_client('s3', region_name='us-east-1')

	# Page with list of article links
	start_urls = ['http://aata.getty.edu/Home']
	# Form input; Categories : (AATA)G9

	# Base URL use for bot's navigation
	BASE_URL = 'http://aata.getty.edu'

	def prase_fullText(self, response):
		"""
		Parse fullText article page and fetch data.
		Each items are processed into the ITEM_PIPELINES before save.
		"""
		raise CloseSpider('Not Implemented yet.')

		# Open article
		article = Article()
		for a in response.css('tr td'):

			# Extract metadata.
			article['fileURL'] = a.css('span::text').extract_first()
			article['fullText'] = a.css('a::text').extract_first()
			article['abstract'] = '1'
			article['topics'] = '1'

			# This line push the item through the pipeline.
			yield article

	def parse_browse(self, response):
		"""
		Parse the main pages and fetch fullText page.
		Each article page is callback through parse_fulltext.
		"""
		raise CloseSpider('Not Implemented yet.')

		data = {
			'__VIEWSTATE': response.css('input#__VIEWSTATE::attr(value)').extract_first(),
			'__EVENTTARGET': 'ctl00$MainContent$ctlNav$TreeViewTOC',
			'__EVENTARGUMENT': "sAATA\\tocG\G_9\\G_9_1",
			'__VIEWSTATEGENERATOR': response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first(),
			'__EVENTVALIDATION': response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
		}

		yield scrapy.FormRequest(url=self.BASE_URL + '/Browse',
									method='POST',
									formdata=data,
									dont_filter=True,
									callback=self.prase_fullText
								)

	def parse(self, response):
		"""
		Simulate scraping AATA sources.
		Parse the .ris file into formated data and push on S3.
		"""

		filepath = 'Abstracts.ris'

		with open(filepath, 'r', encoding="utf-8") as bibliography_file:
			entries = readris(bibliography_file)

			for entry in entries:

				#Map enries inton article.
				article = Article()

				# Extract metadata.
				if 'translated_title' in entry:
					article['title'] = entry['translated_title']
				else:
					article['title'] = entry['title']

				if 'authors' in entry:
					article['authors'] = entry['authors']

				if 'abstract' in entry:
					article['abstract'] = entry['abstract']
					# Use comprehend to add key phrases objects
					comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
					# fullText is too long to be used in AWS Comprehend. Use abstract instead.
					article["topics"] = comprehend.detect_key_phrases(Text=article["abstract"], LanguageCode='en')

				if 'year' in entry:
					article['releaseDate'] = entry['year']

				if 'type_of_reference' in entry:
					article['articleType'] = entry['type_of_reference']

				article['fullText'] = 'none'
				article['fileURL'] = 'none'

				if 'keywords' in entry:
					article['keyWords'] = entry['keywords']

				article['lastUpdate'] = datetime.date.today()

				# This line push the item through the pipeline.
				yield article

		"""
		raise CloseSpider('Not Implemented yet.')
		data = {
			'__VIEWSTATE': response.css('input#__VIEWSTATE::attr(value)').extract_first(),
			'__EVENTTARGET': 'ctl00$NavigationMenu',
			'__EVENTARGUMENT': 'Browse',
			'__VIEWSTATEGENERATOR': response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first(),
			'__EVENTVALIDATION': response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
		}

		yield scrapy.FormRequest(url=self.BASE_URL + '/Browse',
									method='POST',
									formdata=data,
									dont_filter=True,
									callback=self.parse_browse
								)
		"""
