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
	name = "hesc"
	allowed_domains = ['www.heritagesciencejournal.springeropen.com']

	# Boto3 session for S3.
	session = botocore.session.get_session()
	# Has to be in us-east where CloudSearch is avilable.
	client = session.create_client('s3', region_name='us-east-1a')

	# Page with list of article links
	start_urls = ['https://heritagesciencejournal.springeropen.com/articles']
	# Base URL use for bot's navigation
	BASE_URL = 'https://heritagesciencejournal.springeropen.com'

	def prase_fullText(self, response):
		"""
		Parse fullText article page and fetch data.
		Each items are processed into the ITEM_PIPELINES before save.
		"""

		# Open article
		article = Article()
		for a in response.css('main.c-content-layout__main'):

			# Extract metadata.
			soup = BeautifulSoup(a.css('h1.ArticleTitle').extract_first(), 'html.parser')
			article['title'] = soup.get_text()
			#article['title'] = a.css('h1.ArticleTitle').extract_first()

			article['authors'] = a.css('div.AuthorNames li span.AuthorName::text').extract()

			soup = BeautifulSoup(a.css('section.Abstract *.Para').extract_first(), 'html.parser')
			article['abstract'] = soup.get_text()
			#article['abstract'] =  a.css('section.Abstract *.Para').extract_first()

			article['releaseDate'] = a.css('div.ArticleHistory p.HistoryOnlineDate::text').extract_first()
			article['articleType'] = a.css('div.ArticleCategory::text').extract_first()

			soup = BeautifulSoup(a.css('main').extract_first(), 'html.parser')
			article['fullText'] = soup.get_text()

			article['fileURL'] = a.xpath('//a[@id="articlePdf"]/@href').extract_first()
			article['lastUpdate'] = datetime.date.today()

			# Use comprehend to add key phrases objects
			comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
			# fullText is too long to be used in AWS Comprehend. Use abstract instead.
			article["topics"] = comprehend.detect_key_phrases(Text=article["abstract"], LanguageCode='en')

			# This line push the item through the pipeline.
			yield article

	def parse(self, response):
		"""
		Parse the main pages and fetch fullText pageself.
		Each article page is callback through parse_fulltext.
		"""

		# For each article on the current page...
		for a in response.css('ol.c-list-group li.c-list-group__item'):

			# fetch the fullText link.
			fullText_page = a.css('li a::attr(href)').extract()[1]
			if fullText_page is not None:
				yield scrapy.Request(self.BASE_URL + fullText_page, self.prase_fullText, dont_filter=True)

		# Go to the next page is there is any.
		next_page = response.css('a.c-search-navbar__pagination-link--next::attr(href)').extract_first()
		if next_page is not None:
			yield scrapy.Request(self.BASE_URL + next_page, self.parse, dont_filter=True)
