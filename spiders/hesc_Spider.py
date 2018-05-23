import os, io, datetime, re, json

# Scrapy Libraries
import scrapy
from scrapy.spiders import CrawlSpider

# AWS API services
import botocore.session
import boto3

# Import de la class Item Article.
from micorr_crawlers.items.Article import Article, Fields

# BeautifulSoup for cleaning HTML
from bs4 import BeautifulSoup

class hesc_Spider(CrawlSpider):

	# Heritage Science
	# https://heritagesciencejournal.springeropen.com
	name = "hesc"
	allowed_domains = ['www.heritagesciencejournal.springeropen.com']
	# Page with list of article links
	start_urls = ['https://heritagesciencejournal.springeropen.com/articles']
	# Base URL use for bot's navigation
	BASE_URL = 'https://heritagesciencejournal.springeropen.com'

	# Boto3 session for S3.
	session = botocore.session.get_session()
	# Has to be in us-east where CloudSearch is avilable.
	client = session.create_client('s3', region_name='us-east-1a')

	def prase_fullText(self, response):
		"""
		Parse fullText article page and fetch data.
		Each items are processed into the ITEM_PIPELINES before save.
		"""

		# Open article
		article = Article()
		fields = Fields()
		for a in response.css('main.c-content-layout__main'):

			# Extract metadata.
			# Add ID
			article['id'] = re.sub('https://doi.org/', '', a.css('p.ArticleDOI a::text').extract_first())

			# Add title
			soup = BeautifulSoup(a.css('h1.ArticleTitle').extract_first(), 'html.parser')
			fields['title'] = soup.get_text()

			# Add authors
			fields['authors'] = a.css('div.AuthorNames li span.AuthorName::text').extract()

			# Add abstract
			soup = BeautifulSoup(a.css('section.Abstract *.Para').extract_first(), 'html.parser')
			fields['abstract'] = soup.get_text()

			# Add date of publishing
			fields['release_date'] = a.css('div.ArticleHistory p.HistoryOnlineDate::text').extract_first()

			# Add type of article
			fields['article_type'] = a.css('div.ArticleCategory::text').extract_first()

			# Add fulltext.
			soup = BeautifulSoup(a.css('main').extract_first(), 'html.parser')
			fields['fulltext'] = soup.get_text()

			# Add file url
			fields['file_url'] = a.xpath('//a[@id="articlePdf"]/@href').extract_first()


			# Use comprehend to add key phrases objects
			#comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
			# fullText is too long to be used in AWS Comprehend. Use abstract instead.
			#fields["topics"] = comprehend.detect_key_phrases(Text=article["abstract"], LanguageCode='en')

			# Add keywords
			fields['keywords'] = a.css('section.KeywordGroup div *::text').extract()

			# Add last time fetched by bot.
			fields['last_update'] = datetime.date.today()

			# Merge field to article. Requied structure of file for CloudSearch.
			article['fields'] = fields

			# This line push the item through the pipeline.
			yield article

	def parse(self, response):
		"""
		Parse the main pages and fetch fullText page.
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
