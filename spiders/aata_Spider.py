import os, json, io, datetime
from RISparser import readris

import scrapy
from scrapy.spiders import CrawlSpider

from bs4 import BeautifulSoup

# Import de la class Item Article.
from micorr_crawlers.items.Article import Article, Fields

# AWS API services
import botocore.session
import boto3

import re


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

	def parse(self, response):
		"""
		Simulate scraping AATA sources.
		Parse the .ris file into formated data and push on S3.
		"""

		filepath = 'Abstracts.ris'

		with open(filepath, 'r', encoding="utf-8") as bibliography_file:
			entries = readris(bibliography_file)

			for entry in entries:

				#Map enries into article.
				article = Article()
				fields = Fields()


				if 'accession_number' in entry:
					article['id'] = re.sub('[\s+]', '', entry['accession_number'])

				# Add title
				if 'translated_title' in entry:
					fields['title'] = entry['translated_title']
				else:
					fields['title'] = entry['title']

				# Add authors
				if 'authors' in entry:
					fields['authors'] = entry['authors']

				# Add abstract
				if 'abstract' in entry:
					fields['abstract'] = entry['abstract']

					# Add key phrases
					# Use comprehend to add key phrases objects
					#comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')
					# fullText is too long to be used in AWS Comprehend. Use abstract instead.
					#article["topics"] = comprehend.detect_key_phrases(Text=article["abstract"], LanguageCode='en')

				# Add year of publishing
				if 'year' in entry:
					fields['release_date'] = entry['year']

				# Add type of article
				if 'type_of_reference' in entry:
					fields['article_type'] = entry['type_of_reference']

				#article['fullText'] = 'none'
				#article['fileURL'] = 'none'

				# Add keywords
				if 'keywords' in entry:
					fields['keywords'] = entry['keywords']

				# Add last time fetched by bot.
				fields['last_update'] = datetime.date.today()

				# Merge field to article. Requied structure of file for CloudSearch.
				article['fields'] = fields

				# This line push the item through the pipeline.
				yield article
