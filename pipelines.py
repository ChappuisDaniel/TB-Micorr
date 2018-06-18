# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
import boto3
from time import sleep

class DynamoDBStorePipeline(object):
    def process_item(self, item, spider):

        if 'id' in item and 'title' in item:
            # If one is setted, item is passed through.

            # Test each possible empty attribut and set them to Non (null)
            # Otherwise DynamoDB refuses them.
            if 'fulltext' not in item:
                item['fulltext'] = None
            if 'file_url' not in item:
                item['file_url'] = None
            if 'keywords' not in item:
                item['keywords'] = None

            # Get the service resource.
            dynamodb = boto3.resource('dynamodb', region_name="us-east-1")
            table = dynamodb.Table('allScraped')

            response = table.put_item(
                Item={
                    # Those are technical attributes.
                    'id': str(item['id']),
                    'last_update': int(item['last_update']),

                    # Those are mandatory attributs.
                    'title': str(item['title']),
                    'authors': item['authors'],
                    'abstract': str(item['abstract']),
                    'release_date': str(item['release_date']),
                    'article_type': str(item['article_type']),

                    # These fields may be empty.
                    'fulltext': item['fulltext'],
                    'file_url': item['file_url'],
                    'keywords': item['keywords']

                },
                # Assert an article with same ID AND TITLE is not stored twice.
                ConditionExpression='attribute_not_exists(id) AND attribute_not_exists(title)'
            )

            sleep(0.5) # Wait for table write capacity

            return item

        else:
            # Else it is droped.
            raise DropItem("Item usability compromised.")
