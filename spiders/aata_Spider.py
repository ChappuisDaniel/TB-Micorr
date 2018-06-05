import os, io, re, json, time
from datetime import datetime
# Scrapy Libraries
import scrapy
from scrapy.spiders import CrawlSpider
from scrapy.http import *
# BeautifulSoup for cleaning HTML
from bs4 import BeautifulSoup
# Import de la class Item Article.
from micorr_crawlers.items.Article import Article
from RISparser import readris

class aata_Spider(CrawlSpider):

	# AATA
	# http://aata.getty.edu
	name = "aata"
	allowed_domains = ['aata.getty.edu']

	# Get the crawled time for last_update timestamp.
	now = datetime.now()

	# Replace start_urls
	def start_requests(self):
		"""

		"""
		# Send a GET request on top page. Should get a cookie for upcomming uses.
		#url = "http://aata.getty.edu/Home"
		url = 'https://heritagesciencejournal.springeropen.com/articles'
		yield Request(url, self.parse, method="GET")

	def parse_test(self, response):
		"""
		Simulate scraping AATA sources.
		Parse the .ris file into formated data and push on S3.
		"""
		print("____ PARSE ____ " + str(response.headers.getlist('Set-Cookie')))

		# URL for next call.
		url = "http://aata.getty.edu/Browse"

		# Header
		header ={
			"Connection" : "keep-alive",
			"Cache-Control" : "max-age=0",
			"Origin" : "http://aata.getty.edu",
			"Upgrade-Insecure-Requests" : "1",
			"Content-Type" : "application/x-www-form-urlencoded",
			"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
			"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Referer" : "http://aata.getty.edu/Home",
			"Accept-Encoding" : "gzip, deflate",
			"Accept-Language" : "fr-CH,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6"
		}

		# Body
		body = {
			"__eo_obj_states" : "ASEBGwpTcGxpdHRlcjEhAggHMDowfDE1MQUEMTowfA==",
			"__eo_sc" : "",
			"__EVENTTARGET" : "ctl00",
			"__EVENTARGUMENT" : "sAATA\tocG\G_9\G_9_1",
			"__LASTFOCUS" : "",
			"__VIEWSTATE" : "/wEPDwUKMjE0NjUwOTE0NQ9kFgJmD2QWAgIDD2QWBAITDzwrAA0BDDwrAAcBBBQrAAIWAh4ISW1hZ2VVcmwFIn4vQXNzZXRzL0ltYWdlcy90YWItcmVzdWx0cy1vbi5wbmdkZAIVD2UWBGYPZBYCAgEPDxYCHgdWaXNpYmxlZ2QWAmYPZBYSAgMPZBYCAgEPDxYGHglGb3JlQ29sb3IJZmZm/x4JQmFja0NvbG9yCbPG0P8eBF8hU0ICDBYCHgVzdHlsZQUPY3Vyc29yOkRlZmF1bHQ7ZAIJDw8WAh8BZ2RkAg8PDxYCHwFnZBYKZg9kFgJmDxAPFgIeB0NoZWNrZWRoZGRkZAIBD2QWAmYPEA8WAh8GaGRkZGQCAg9kFgJmDxAPFgIfBmhkZGRkAgMPZBYCZg8QDxYCHwZoZGRkZAIED2QWAmYPEA8WAh8GaGRkZGQCEQ8PFgIfAWdkFgICAQ8PFgIeBFRleHQFC01vcmUuLi4gKDgpZGQCFQ8PFgIfAWdkFgpmD2QWAmYPEA8WAh8GaGRkZGQCAQ9kFgJmDxAPFgIfBmhkZGRkAgIPZBYCZg8QDxYCHwZoZGRkZAIDD2QWAmYPEA8WAh8GaGRkZGQCBA9kFgJmDxAPFgIfBmhkZGRkAhcPDxYCHwFnZBYCAgEPDxYCHwcFDE1vcmUuLi4gKDQxKWRkAhsPDxYCHwFnZBYSZg9kFgJmDxAPFgIfBmhkZGRkAgEPZBYCZg8QDxYCHwZoZGRkZAICD2QWAmYPEA8WAh8GaGRkZGQCAw9kFgJmDxAPFgIfBmhkZGRkAgQPZBYCZg8QDxYCHwZoZGRkZAIFD2QWAmYPEA8WAh8GaGRkZGQCBg9kFgJmDxAPFgIfBmhkZGRkAgcPZBYCZg8QDxYCHwZoZGRkZAIID2QWAmYPEA8WAh8GaGRkZGQCHw8PFgIfAWdkFgpmD2QWAmYPEA8WAh8GaGRkZGQCAQ9kFgJmDxAPFgIfBmhkZGRkAgIPZBYCZg8QDxYCHwZoZGRkZAIDD2QWAmYPEA8WAh8GaGRkZGQCBA9kFgJmDxAPFgIfBmhkZGRkAiEPDxYCHwFnZBYCAgEPDxYCHwcFEk5leHQgMjAuLi4gKDE1ODI2KWRkAgEPZBYCAgEPZBYEAgEPDxYCHwFoZGQCAw8PFgIfAWdkFggCAQ9kFgJmD2QWCGYPZBYEZg8QDxYCHwZnZGRkZAIBDw8WAh8HBQxEZXNlbGVjdCBBbGxkZAIBD2QWBGYPEA8WAh8GZ2RkZGQCAQ8PFgIfBwUNRGVzZWxlY3QgUGFnZWRkAgQPZBYCZg8QZBAVBAIxMAIyMAI1MAMxMDAVBAIxMAIyMAI1MAMxMDAUKwMEZ2dnZxYBAgFkAggPZBYCZg8QDxYCHwZnZGRkZAIDD2QWAgIBDw8WAh8HBR1TRUFSQ0g6IE5hdmlnYXRpb246IEFBVEEgLSBHOWRkAgUPFCsAAmQQFgAWABYAFgJmD2QWBgIBDw8WAh8HBQExZGQCBQ8PFgIfBwUCMjBkZAIJDw8WAh8HBQUxMzE0NmRkAgkPFCsAAhYCHwFnEBYAFgAWABYCZg9kFgYCAQ8PFgIfBwUBMWRkAgUPDxYCHwcFAjIwZGQCCQ8PFgIfBwUFMTMxNDZkZBgEBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WOQUOY3RsMDAkaWJFeWVmdWwFGGN0bDAwJGN0bEZhY2V0JGlidFNvdXJjZQUZY3RsMDAkY3RsRmFjZXQkaWJ0RG9jVHlwZQUUY3RsMDAkY3RsRmFjZXQkY2hrSkEFFGN0bDAwJGN0bEZhY2V0JGNoa0JBBRRjdGwwMCRjdGxGYWNldCRjaGtCVwUUY3RsMDAkY3RsRmFjZXQkY2hrVEgFFGN0bDAwJGN0bEZhY2V0JGNoa1BBBRpjdGwwMCRjdGxGYWNldCRpYnRMYW5ndWFnZQUVY3RsMDAkY3RsRmFjZXQkY2hrRU5HBRVjdGwwMCRjdGxGYWNldCRjaGtHRVIFFWN0bDAwJGN0bEZhY2V0JGNoa0ZSRQUVY3RsMDAkY3RsRmFjZXQkY2hrSVRBBRVjdGwwMCRjdGxGYWNldCRjaGtDSEkFGWN0bDAwJGN0bEZhY2V0JGlidFB1YkRhdGUFG2N0bDAwJGN0bEZhY2V0JGNoazIwMTAtMjAxOAUbY3RsMDAkY3RsRmFjZXQkY2hrMjAwMC0yMDA5BRtjdGwwMCRjdGxGYWNldCRjaGsxOTkwLTE5OTkFG2N0bDAwJGN0bEZhY2V0JGNoazE5ODAtMTk4OQUbY3RsMDAkY3RsRmFjZXQkY2hrMTk3MC0xOTc5BRtjdGwwMCRjdGxGYWNldCRjaGsxOTYwLTE5NjkFG2N0bDAwJGN0bEZhY2V0JGNoazE5NTAtMTk1OQUXY3RsMDAkY3RsRmFjZXQkY2hrMTk1MF8FGWN0bDAwJGN0bEZhY2V0JGNoa1Vua25vd24FGGN0bDAwJGN0bEZhY2V0JGlidEF1dGhvcgUTY3RsMDAkY3RsRmFjZXQkYWNiMQUTY3RsMDAkY3RsRmFjZXQkYWNiMgUTY3RsMDAkY3RsRmFjZXQkYWNiMwUTY3RsMDAkY3RsRmFjZXQkYWNiNAUTY3RsMDAkY3RsRmFjZXQkYWNiNQUeY3RsMDAkTWFpbkNvbnRlbnQkY2hrU2VsZWN0QWxsBR9jdGwwMCRNYWluQ29udGVudCRjaGtTZWxlY3RQYWdlBRxjdGwwMCRNYWluQ29udGVudCRpYkRvd25sb2FkBRljdGwwMCRNYWluQ29udGVudCRpYlByaW50BSFjdGwwMCRNYWluQ29udGVudCRjaGtTaG93QWJzdHJhY3QFJGN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRpYlByZWZIRAUrY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGliSERfUmVjQ2hlY2tlZAUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwwJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwyJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwzJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw0JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw1JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw2JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw3JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw4JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw5JGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxMCRjYl8FJmN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRjdHJsMTEkY2JfBSZjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEkY3RybDEyJGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxMyRjYl8FJmN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRjdHJsMTQkY2JfBSZjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEkY3RybDE1JGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxNiRjYl8FJmN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRjdHJsMTckY2JfBSZjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEkY3RybDE4JGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxOSRjYl8FHGN0bDAwJE1haW5Db250ZW50JERhdGFQYWdlcjIPFCsABGRkAhQC2mZkBRtjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEPFCsADmRkZGRkZGQ8KwAUAALaZmRkZGYCFGQFHGN0bDAwJE1haW5Db250ZW50JERhdGFQYWdlcjEPFCsABGRkAhQC2mZkGh7pncLrb0BMC+e+C7KK8zSO2Z6VQkSRQMIflJ9cnmo=",
			"__VIEWSTATEGENERATOR" : "1864AA6B",
			"__EVENTVALIDATION" : "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",
			"ctl00$prefInput" : "",
			"eo_version" : "8.0.51.2",
			"eo_style_keys" : "/wFk"
		}

		# Send post request, should set seaarch for Results page.
		yield Request(url, self.parse_result, method="POST", headers=header, body=json.dumps(body))


	def parse_result(self, response):
		"""
		Simulate scraping AATA sources.
		Parse the .ris file into formated data and push on S3.
		"""
		print("____ PARSE ____ " + str(response.headers.getlist('Set-Cookie')))

		# URL for next call.
		url = "http://aata.getty.edu/Results"

		# Header
		header ={
			"Connection" : "keep-alive",
			"Cache-Control" : "max-age=0",
			"Origin" : "http://aata.getty.edu",
			"Upgrade-Insecure-Requests" : "1",
			"Content-Type" : "application/x-www-form-urlencoded",
			"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
			"Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Referer" : "http://aata.getty.edu/Browse",
			"Accept-Encoding" : "gzip, deflate",
			"Accept-Language" : "fr-CH,fr-FR;q=0.9,fr;q=0.8,en-US;q=0.7,en;q=0.6"
		}

		# Body
		body = {
	        "__eo_obj_states" : "ASEBGwpTcGxpdHRlcjEhAggHMDowfDE1MQUEMTowfA==",
			"__eo_sc" : "",
			"__EVENTTARGET" : "ctl00$MainContent$lbDownload",
			"__EVENTARGUMENT" : "",
			"__LASTFOCUS" : "",
			"__VIEWSTATE" : "/wEPDwUKMjE0NjUwOTE0NQ9kFgJmD2QWAgIDD2QWBAITDzwrAA0BDDwrAAcBBBQrAAIWAh4ISW1hZ2VVcmwFIn4vQXNzZXRzL0ltYWdlcy90YWItcmVzdWx0cy1vbi5wbmdkZAIVD2UWBGYPZBYCAgEPDxYCHgdWaXNpYmxlZ2QWAmYPZBYSAgMPZBYCAgEPDxYGHglGb3JlQ29sb3IJZmZm/x4JQmFja0NvbG9yCbPG0P8eBF8hU0ICDBYCHgVzdHlsZQUPY3Vyc29yOkRlZmF1bHQ7ZAIJDw8WAh8BZ2RkAg8PDxYCHwFnZBYKZg9kFgJmDxAPFgIeB0NoZWNrZWRoZGRkZAIBD2QWAmYPEA8WAh8GaGRkZGQCAg9kFgJmDxAPFgIfBmhkZGRkAgMPZBYCZg8QDxYCHwZoZGRkZAIED2QWAmYPEA8WAh8GaGRkZGQCEQ8PFgIfAWdkFgICAQ8PFgIeBFRleHQFC01vcmUuLi4gKDgpZGQCFQ8PFgIfAWdkFgpmD2QWAmYPEA8WAh8GaGRkZGQCAQ9kFgJmDxAPFgIfBmhkZGRkAgIPZBYCZg8QDxYCHwZoZGRkZAIDD2QWAmYPEA8WAh8GaGRkZGQCBA9kFgJmDxAPFgIfBmhkZGRkAhcPDxYCHwFnZBYCAgEPDxYCHwcFDE1vcmUuLi4gKDQxKWRkAhsPDxYCHwFnZBYSZg9kFgJmDxAPFgIfBmhkZGRkAgEPZBYCZg8QDxYCHwZoZGRkZAICD2QWAmYPEA8WAh8GaGRkZGQCAw9kFgJmDxAPFgIfBmhkZGRkAgQPZBYCZg8QDxYCHwZoZGRkZAIFD2QWAmYPEA8WAh8GaGRkZGQCBg9kFgJmDxAPFgIfBmhkZGRkAgcPZBYCZg8QDxYCHwZoZGRkZAIID2QWAmYPEA8WAh8GaGRkZGQCHw8PFgIfAWdkFgpmD2QWAmYPEA8WAh8GaGRkZGQCAQ9kFgJmDxAPFgIfBmhkZGRkAgIPZBYCZg8QDxYCHwZoZGRkZAIDD2QWAmYPEA8WAh8GaGRkZGQCBA9kFgJmDxAPFgIfBmhkZGRkAiEPDxYCHwFnZBYCAgEPDxYCHwcFEk5leHQgMjAuLi4gKDE1ODI2KWRkAgEPZBYCAgEPZBYEAgEPDxYCHwFoZGQCAw8PFgIfAWdkFggCAQ9kFgJmD2QWCGYPZBYEZg8QDxYCHwZnZGRkZAIBDw8WAh8HBQxEZXNlbGVjdCBBbGxkZAIBD2QWBGYPEA8WAh8GZ2RkZGQCAQ8PFgIfBwUNRGVzZWxlY3QgUGFnZWRkAgQPZBYCZg8QZBAVBAIxMAIyMAI1MAMxMDAVBAIxMAIyMAI1MAMxMDAUKwMEZ2dnZxYBAgFkAggPZBYCZg8QDxYCHwZnZGRkZAIDD2QWAgIBDw8WAh8HBR1TRUFSQ0g6IE5hdmlnYXRpb246IEFBVEEgLSBHOWRkAgUPFCsAAmQQFgAWABYAFgJmD2QWBgIBDw8WAh8HBQExZGQCBQ8PFgIfBwUCMjBkZAIJDw8WAh8HBQUxMzE0NmRkAgkPFCsAAhYCHwFnEBYAFgAWABYCZg9kFgYCAQ8PFgIfBwUBMWRkAgUPDxYCHwcFAjIwZGQCCQ8PFgIfBwUFMTMxNDZkZBgEBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WOQUOY3RsMDAkaWJFeWVmdWwFGGN0bDAwJGN0bEZhY2V0JGlidFNvdXJjZQUZY3RsMDAkY3RsRmFjZXQkaWJ0RG9jVHlwZQUUY3RsMDAkY3RsRmFjZXQkY2hrSkEFFGN0bDAwJGN0bEZhY2V0JGNoa0JBBRRjdGwwMCRjdGxGYWNldCRjaGtCVwUUY3RsMDAkY3RsRmFjZXQkY2hrVEgFFGN0bDAwJGN0bEZhY2V0JGNoa1BBBRpjdGwwMCRjdGxGYWNldCRpYnRMYW5ndWFnZQUVY3RsMDAkY3RsRmFjZXQkY2hrRU5HBRVjdGwwMCRjdGxGYWNldCRjaGtHRVIFFWN0bDAwJGN0bEZhY2V0JGNoa0ZSRQUVY3RsMDAkY3RsRmFjZXQkY2hrSVRBBRVjdGwwMCRjdGxGYWNldCRjaGtDSEkFGWN0bDAwJGN0bEZhY2V0JGlidFB1YkRhdGUFG2N0bDAwJGN0bEZhY2V0JGNoazIwMTAtMjAxOAUbY3RsMDAkY3RsRmFjZXQkY2hrMjAwMC0yMDA5BRtjdGwwMCRjdGxGYWNldCRjaGsxOTkwLTE5OTkFG2N0bDAwJGN0bEZhY2V0JGNoazE5ODAtMTk4OQUbY3RsMDAkY3RsRmFjZXQkY2hrMTk3MC0xOTc5BRtjdGwwMCRjdGxGYWNldCRjaGsxOTYwLTE5NjkFG2N0bDAwJGN0bEZhY2V0JGNoazE5NTAtMTk1OQUXY3RsMDAkY3RsRmFjZXQkY2hrMTk1MF8FGWN0bDAwJGN0bEZhY2V0JGNoa1Vua25vd24FGGN0bDAwJGN0bEZhY2V0JGlidEF1dGhvcgUTY3RsMDAkY3RsRmFjZXQkYWNiMQUTY3RsMDAkY3RsRmFjZXQkYWNiMgUTY3RsMDAkY3RsRmFjZXQkYWNiMwUTY3RsMDAkY3RsRmFjZXQkYWNiNAUTY3RsMDAkY3RsRmFjZXQkYWNiNQUeY3RsMDAkTWFpbkNvbnRlbnQkY2hrU2VsZWN0QWxsBR9jdGwwMCRNYWluQ29udGVudCRjaGtTZWxlY3RQYWdlBRxjdGwwMCRNYWluQ29udGVudCRpYkRvd25sb2FkBRljdGwwMCRNYWluQ29udGVudCRpYlByaW50BSFjdGwwMCRNYWluQ29udGVudCRjaGtTaG93QWJzdHJhY3QFJGN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRpYlByZWZIRAUrY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGliSERfUmVjQ2hlY2tlZAUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwwJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwyJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwzJGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw0JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw1JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw2JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw3JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw4JGNiXwUlY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmw5JGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxMCRjYl8FJmN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRjdHJsMTEkY2JfBSZjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEkY3RybDEyJGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxMyRjYl8FJmN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRjdHJsMTQkY2JfBSZjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEkY3RybDE1JGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxNiRjYl8FJmN0bDAwJE1haW5Db250ZW50JExpc3RWaWV3MSRjdHJsMTckY2JfBSZjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEkY3RybDE4JGNiXwUmY3RsMDAkTWFpbkNvbnRlbnQkTGlzdFZpZXcxJGN0cmwxOSRjYl8FHGN0bDAwJE1haW5Db250ZW50JERhdGFQYWdlcjIPFCsABGRkAhQC2mZkBRtjdGwwMCRNYWluQ29udGVudCRMaXN0VmlldzEPFCsADmRkZGRkZGQ8KwAUAALaZmRkZGYCFGQFHGN0bDAwJE1haW5Db250ZW50JERhdGFQYWdlcjEPFCsABGRkAhQC2mZkGh7pncLrb0BMC+e+C7KK8zSO2Z6VQkSRQMIflJ9cnmo=",
			"__VIEWSTATEGENERATOR" : "1864AA6B",
			"__EVENTVALIDATION" : "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",
			"ctl00$prefInput" : "",
			"eo_version" : "8.0.51.2",
			"eo_style_keys" : "/wFk",
			"ctl00$MainContent$chkSelectAll" : "on",
			"ctl00$MainContent$chkSelectPage" : "on",
			"ctl00$MainContent$ddlRecPerPage" : "20",
			"ctl00$MainContent$txbSearch" : "",
			"ctl00$MainContent$chkShowAbstract" : "on",
			"ctl00$MainContent$ListView1$ctrl0$cb_" : "on"
	    }

		# Send post request, should provide the Results page with active serach.
		yield Request(url, self.parse_file, method="POST", headers=header, body=json.dumps(body))


	def parse(self, response):
		"""
		Parse .ris file and submit article to DynamoDB table.
		"""
		filepath = 'Abstracts.ris'

		with open(filepath, 'r', encoding="utf-8") as bibliography_file:
			entries = readris(bibliography_file)

			for entry in entries:

				#Map enries into article.
				article = Article()

				if 'accession_number' in entry:
					article['id'] = re.sub('[\s+]', '', entry['accession_number'])

				# Add title
				if 'translated_title' in entry:
					article['title'] = entry['translated_title']
				else:
					article['title'] = entry['title']

				# Add authors
				if 'authors' in entry:
					article['authors'] = entry['authors']

				# Add abstract
				if 'abstract' in entry:
					article['abstract'] = entry['abstract']

				# Add year of publishing
				if 'year' in entry:
					article['release_date'] = entry['year']

				# Add type of article
				if 'type_of_reference' in entry:
					article['article_type'] = entry['type_of_reference']

				# Add keywords
				if 'keywords' in entry:
					article['keywords'] = entry['keywords']

				# Add last time fetched by bot.
				article['last_update'] = int(time.mktime(self.now.timetuple()))

				# This line push the item through the pipeline.
				yield article
