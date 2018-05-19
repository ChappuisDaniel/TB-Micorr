# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem

class MicorrPipeline(object):
    def process_item(self, item, spider):
        """
        Test if the current item has a setted fullText attribut.
        """

        # Test fullText attribut
        if 'title' in item:
            # If one is setted, item is passed through.
            return item
        else:
            # Else it is droped.
            raise DropItem("Item integrity compromised.")
