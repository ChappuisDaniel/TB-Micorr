import os, io, re, json, time
from datetime import datetime
# Scrapy Libraries
import scrapy
from scrapy.spiders import CrawlSpider
# BeautifulSoup for cleaning HTML
from bs4 import BeautifulSoup
# Import de la class Item Article.
from micorr_crawlers.items.Article import Article

class hesc_Spider(CrawlSpider):

	# Heritage Science
	# https://heritagesciencejournal.springeropen.com
	name = "hesc"
	allowed_domains = ['www.heritagesciencejournal.springeropen.com']
	# Page with list of article links
	start_urls = ['https://heritagesciencejournal.springeropen.com/articles']
	# Base URL use for bot's navigation
	BASE_URL = 'https://heritagesciencejournal.springeropen.com'

	# Get the crawled time for last_update timestamp.
	now = datetime.now()

	def prase_fullText(self, response):
		"""
		Parse fullText article page and fetch data.
		Each items are processed into the ITEM_PIPELINES before save.
		"""

		# Open article
		article = Article()
		#fields = Fields()
		for a in response.css('main.c-content-layout__main'):

			# Extract metadata.
			# Add ID
			article['id'] = re.sub('https://doi.org/10.1186/', '', a.css('p.ArticleDOI a::text').extract_first())

			# Add title
			soup = BeautifulSoup(a.css('h1.ArticleTitle').extract_first(), 'html.parser')
			article['title'] = soup.get_text()

			# Add authors
			article['authors'] = a.css('div.AuthorNames li span.AuthorName::text').extract()

			# Add abstract
			soup = BeautifulSoup(a.css('section.Abstract *.Para').extract_first(), 'html.parser')
			article['abstract'] = soup.get_text()

			# Add date of publishing
			article['release_date'] = a.css('div.ArticleHistory p.HistoryOnlineDate::text').extract_first()

			# Add type of article
			article['article_type'] = a.css('div.ArticleCategory::text').extract_first()

			# Add fulltext.
			soup = BeautifulSoup(a.css('main').extract_first(), 'html.parser')
			article['fulltext'] = soup.get_text()

			# Add file url
			article['file_url'] = a.xpath('//a[@id="articlePdf"]/@href').extract_first()

			# Add keywords
			article['keywords'] = a.css('section.KeywordGroup div *::text').extract()

			# Add last time fetched by bot.
			article['last_update'] = int(time.mktime(self.now.timetuple()))

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
