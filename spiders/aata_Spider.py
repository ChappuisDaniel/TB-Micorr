import os, io, datetime, re, json

# Scrapy Libraries
import scrapy
from scrapy.spiders import CrawlSpider

from selenium import webdriver

# AWS API services
import botocore.session
import boto3

# Import de la class Item Article.
from micorr_crawlers.items.Article import Article, Fields

# RIS parser from : https://github.com/MrTango/RISparser
from RISparser import readris


class aata_Spider(CrawlSpider):

	# AATA
	# http://aata.getty.edu
	name = "aata"
	allowed_domains = ['aata.getty.edu']
	# Page with list of article links
	start_urls = ['http://aata.getty.edu/Home']
	# Base URL use for bot's navigation
	BASE_URL = 'http://aata.getty.edu'

	# Boto3 session for S3.
	session = botocore.session.get_session()
	# Has to be in us-east where CloudSearch is avilable.
	client = session.create_client(service_name='s3', region_name='us-east-1')
	#comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')

	def __init__(self):

		profile = webdriver.FirefoxProfile()
		profile.set_preference('browser.download.folderList', 2) # custom location
		profile.set_preference('browser.download.manager.showWhenStarting', False)
		profile.set_preference('browser.download.dir', '/tmp')
		profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/ris')

		browser = webdriver.Firefox(profile)


	def parse(self, response):
		self.driver.get('http://aata.getty.edu/Home')

		next = self.driver.find_element_by_xpath('/Home')
		next.open()

		next = self.driver.find_element_by_xpath("//div[@id='NavigationMenu']/ul/li[2]/a/img")
		next.click()
		time.sleep(2.5)

		next = self.driver.find_element_by_xpath('css=img[alt="Expand G. Materials and objects: analysis, treatment and techniques"]')
		next.click()
		time.sleep(2.5)

		next = self.driver.find_element_by_xpath('css=img[alt="Expand 9. Metals and metallurgical by-products"]')
		next.click()
		time.sleep(2.5)

		next = self.driver.find_element_by_xpath('id=MainContent_ctlNav_TreeViewTOCt50')
		next.click()
		time.sleep(2.5)

		next = self.driver.find_element_by_xpath('id=MainContent_chkSelectAll')
		next.click()
		time.sleep(2.5)

		next = self.driver.find_element_by_xpath('id=MainContent_lbDownload')
		next.click()
		time.sleep(5)

		self.parse_ris

		self.driver.close()

	def parse_ris(self):
		"""
		Simulate scraping AATA sources.
		Parse the .ris file into formated data and push on S3.
		"""

		filepath = 'tmp/Abstracts.ris'

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

					# fullText is too long to be used in AWS Comprehend. Use abstract instead.
					#article["topics"] = comprehend.detect_key_phrases(Text=article["abstract"], LanguageCode='en')

				# Add year of publishing
				if 'year' in entry:
					fields['release_date'] = entry['year']

				# Add type of article
				if 'type_of_reference' in entry:
					fields['article_type'] = entry['type_of_reference']

				article['fulltext'] = 'none'
				article['file_url'] = 'none'

				# There is no need to add empty field for indexing.

				# Add keywords
				if 'keywords' in entry:
					fields['keywords'] = entry['keywords']

				# Add last time fetched by bot.
				fields['last_update'] = datetime.date.today()

				# Merge field to article. Requied structure of file for CloudSearch.
				article['fields'] = fields

				# This line push the item through the pipeline.
				yield article
