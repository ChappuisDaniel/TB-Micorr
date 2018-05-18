import scrapy
from scrapy.spiders import CrawlSpider

import datetime
import json
from bs4 import BeautifulSoup

# Import de la class Item Article.
from micorr_crawlers.items.Article import Article

# AWS API services
import botocore.session
import boto3

class hesc_Spider(CrawlSpider):

	# Heritage Science
	# https://heritagesciencejournal.springeropen.com
	name = "aata"
	allowed_domains = ['aata.getty.edu']

	# Boto3 session for S3.
	session = botocore.session.get_session()
	# Has to be in us-east where CloudSearch is avilable.
	client = session.create_client('s3', region_name='us-east-1a')

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
			article['fileURL'] = a.xpath('//span[@id="MainContent_ListView1_lbAbs__0"]/@text').extract_first()
			article['abstract'] = '1'
			article['topics'] = '1'

			# This line push the item through the pipeline.
			yield article

	def parse_articlesPage(self, response):
		raise CloseSpider('Not Implemented yet.')

		#javascript:__doPostBack('ctl00$MainContent$ctlNav$TreeViewTOC','sAATA\\tocG\\G_9\\G_9_1')
		data = {
			'__VIEWSTATE': response.css('input#__VIEWSTATE::attr(value)').extract_first(),
			'__EVENTTARGET': 'ctl00$MainContent$ctlNav$TreeViewTOC',
			'__EVENTARGUMENT': "sAATA\\tocG\\G_9\\G_9_1",
			'__VIEWSTATEGENERATOR': response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first(),
			'__EVENTVALIDATION': response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
		}

		yield scrapy.FormRequest(url=self.BASE_URL + '/Browse',
									formdata=data,
									meta = {'dont_redirect': True, 'handle_httpstatus_list': [302]},
									dont_filter=True,
									callback=self.prase_fullText
								)

		"""
		yield scrapy.FormRequest.from_response(
            response,
			formname="Form1",
			formxpath="//form[@id='Form1']",
			method='POST',
            formdata=data,
			dont_filter=True,
            callback=self.prase_fullText
        )
		"""

	def parse(self, response):
		"""
		Parse the main pages and fetch fullText page.
		Each article page is callback through parse_fulltext.
		"""

		data = {
			'__VIEWSTATE': response.css('input#__VIEWSTATE::attr(value)').extract_first(),
			'__EVENTTARGET': 'ctl00$NavigationMenu',
			'__EVENTARGUMENT': 'Browse',
			'__VIEWSTATEGENERATOR': response.css('input#__VIEWSTATEGENERATOR::attr(value)').extract_first(),
			'__EVENTVALIDATION': response.css('input#__EVENTVALIDATION::attr(value)').extract_first()
		}

		yield scrapy.FormRequest(url=self.BASE_URL + '/Browse',
									formdata=data,
									meta = {'dont_redirect': True, 'handle_httpstatus_list': [302]},
									dont_filter=True,
									callback=self.parse_articlesPage
								)

		#raise CloseSpider('Not Implemented yet.')
