# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
import boto3
from time import sleep

class MicorrPipeline(object):
    def process_item(self, item, spider):
        """
        Test if the current item has a setted fullText attribut.
        """

        # Test id attribut
        if 'id' in item:
            # If one is setted, item is passed through.
            return item
        else:
            # Else it is droped.
            raise DropItem("Item integrity compromised.")

class DynamoDBStorePipeline(object):
    def process_item(self, item, spider):
        # Get the service resource.
        dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
        table = dynamodb.Table('allScraped')

        table.put_item(
            Item={
                'id': str(item['id']),
                'last_update': int(item['last_update']),

                'title': str(item['title']),
                'authors': item['authors'],
                'abstract': str(item['abstract']),
                'release_date': str(item['release_date']),
                'article_type': str(item['article_type']),
                # If no fulltext exist store empty string.
                'fulltext': str(item['fulltext']),
                'file_url': str(item['file_url']),
                'keywords': item['keywords']

            },
            # Assert an article with same ID AND TITLE is not stored twice.
            ConditionExpression='attribute_not_exists(id) AND attribute_not_exists(title)'
        )
        sleep(2) # Wait for table write capacity

        return item
