# Micorr-Crawlers
Scrapy bot for MiCorr

This repo contains the source code for bots using Scrapy. Their goal is to crawl research journal and scrap data about the article.
To use them, follow the steps bellow.

## Installation
On Windows we need to install a Python environment. [Miniconda](https://conda.io/miniconda.html) work perfectly fine for the job.
Once it is installed, run the Anaconda Prompt and the followings commands to install Scrapy framework and the needed Boto3 library for AWS.

> conda install -c conda-forge scrapy 

> conda install -c anaconda boto3 

Plese note that boto needs AWS user keys to allow the scripts to work wit AWS APIs. Refere to AWS documentation to learn how to assign premissions to a user and get the key pair.

We need to install BeatifulSoup Library. It is use to clean fetched data of all HTML tags and clean the text we'll submit to AWS Comprehend.

> pip install beautifulsoup4

Installation is ready.

## Configuration AWSCLI
AWSCLI is needed to allow our robot to call for Amazon Services.

> conda install -c conda-forge awscli

When the installation is completed, run the following command to add AWS creditentials. Ensure an AWS user with required acces is  created before.

> aws configure

## Setup
We need to create a blank project to provide the basic structure. Simply run:

> scrapy startproject micorr_crawlers

Now we can fork in the project.

## Overview
For better understanding here is a overview of the main files.

All the bot behavior code are under **/spiders/** folder. The only spider working now is **hesc_Spider.py**.

Spider use items whils scraping. Those are define in **/items/Article.py** file.

The file **settings_SAMPLE.py** define the behavior of all bots in the project and store private information about Amazon Web Services.
Please take care to fill the bank with your own and rename the file **settings.py**.

## Documentation
Here is [Scrapy](https://doc.scrapy.org/en/latest/index.html) and [Boto3](https://boto3.readthedocs.io/en/latest/) documentation.


