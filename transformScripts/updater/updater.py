from __future__ import print_function # Python 2/3 compatibility

import boto3
from boto3.dynamodb.conditions import Key, Attr

import json, csv
from bson import json_util

import decimal, time
from time import sleep
from datetime import datetime

from subprocess import check_output, call, run

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def timeout():
        raise Exception("Waiting table 'allScraped' timeout.")

# Set AWS DynamoDB parameters
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
allScraped_table = dynamodb.Table('allScraped')

# Get the current time for the upcomming update.
now = int(time.mktime(datetime.now().timetuple()))

# Fetch last update time. Use for query.
lastUpdate_file = open("lastUpdate.txt", 'r', encoding="utf-8")
lastUpdate = int(lastUpdate_file.read())
lastUpdate_file.close()

# Wait until table is active.
call = 0
while True:
    response = dynamodb_client.describe_table(TableName='allScraped')
    if response['Table']['TableStatus'] == 'ACTIVE':
        print("Table status 'allScraped' : " + response['Table']['TableStatus'])
        break
    else:
        print("Table status 'allScraped' : " + response['Table']['TableStatus'] + "\n Waiting...")
        call += 1
        sleep(5) # Time in seconds.
        # Call timeout.
        if call > 6:
            timeout()

print("Update new documents from 'allScraped'.")
# Fetch new documents.
result_items = []

response = allScraped_table.scan(
    IndexName = "last_update-id-index",
    FilterExpression = Key('last_update').between(lastUpdate, now)
    )

result_items.extend(response['Items'])

# Use this bloc for querying
while 'LastEvaluatedKey' in response:
    response = allScraped_table.scan(
        IndexName = "last_update-id-index",
        FilterExpression = Key('last_update').between(lastUpdate, now),
        ExclusiveStartKey = response['LastEvaluatedKey']
    )

    result_items.extend(response['Items'])


print("New items found : " + str(len(result_items)))
# Update CloudSearch
print("Create JSON file.")

docCount = 0
itemsCount = 0

# JOSNify
batch = []
for i in result_items:
    # Build doc
    doc = {}

    doc['id'] = i['id']
    doc['type'] = 'add'
    doc['fields'] = {}

    doc['fields']['title'] = i['title']
    doc['fields']['authors'] = i['authors']
    doc['fields']['abstract'] = i['abstract']
    doc['fields']['release_date'] = i['release_date']
    doc['fields']['article_type'] = i['article_type']

    if i['file_url'] != None:
        doc['fields']['file_url'] = i['file_url']

    if i['keywords'] != None:
        doc['fields']['keywords'] = i['keywords']

    # Create fullext field only if there is one. Avoid empty field.
    if i['fulltext'] != None:
        doc['fields']['fulltext'] = i['fulltext']

    doc['fields']['last_update'] = int(i['last_update'])

    batch.append(doc)
    itemsCount += 1
    sleep(0.001) # Wait a bit.

    if itemsCount > 4000 or i == result_items[len(result_items)-1]:
        # Create file
        updateCloudSearch_file = open("updateDoc_" + str(docCount) + ".json", 'w', encoding="utf-8")
        updateCloudSearch_file.write(json.dumps(batch))
        print("Update file n°" + str(docCount) + " complete with " + str(itemsCount) + " documents.")
        updateCloudSearch_file.close()

        docCount += 1
        itemsCount = 0
        batch = []

if len(result_items) > 0:
    print("Start indexing.")
    for doc in range(docCount):
        print("Upload file n°" + str(doc) + " with " + str(itemsCount) + " documents.")
        # Call upload
        docEd = 'http://doc-micorr-test-yzjuar4kajhkoii2hgziiq5vxy.us-east-1.cloudsearch.amazonaws.com'
        updateFile = "updateDoc_" + str(doc) + ".json"
        run(["aws", "cloudsearchdomain", "--endpoint-url", docEd, "upload-documents", "--content-type", "application/json", "--documents", updateFile])
else:
    print("Nothing to index.")

###____________________
# Update lastUpdate.txt
lastUpdate_file = open("lastUpdate.txt", 'w', encoding="utf-8")
lastUpdate_file.write(str(now))
print("Update time set to : " + str(now))
lastUpdate_file.close()
