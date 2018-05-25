# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
import boto3

class MicorrPipeline(object):
    def process_item(self, item, spider):
        """
        Test if the current item has a setted fullText attribut.
        """

        # Test fullText attribut
        if 'id' in item:
            # If one is setted, item is passed through.
            item['type'] = 'add'
            return item
        else:
            # Else it is droped.
            raise DropItem("Item integrity compromised.")

class DynamoDBStorePipeline(object):
    def process_item(self, item, spider):
        # Get the service resource.
        dynamodb = boto3.resource('dynamodb', region_name="us-east-1")

        table = dynamodb.Table('scrapy_testMaj')

        table.put_item(
            Item={
                'id': str(item['id']),
                'last_update': str(item['last_update']),
                'title': str(item['title']),
                'authors': item['authors'],
                'abstract': str(item['abstract']),
                'release_date': str(item['release_date']),
                'article_type': str(item['article_type']),
                #'fulltext': str(item['feilds']['fulltext']),
                'file_url': str(item['file_url']),
                'keywords': item['keywords']
                #'topics': item['feilds']['topics'],

            }
        )
        return item
