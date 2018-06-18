from __future__ import print_function # Python 2/3 compatibility

import boto3
from boto3.dynamodb.conditions import Key, Attr

import  tarfile
import json, csv

import pandas as pd
from pandas.io.json import json_normalize
from itertools import groupby
from collections import OrderedDict

from unflatten import unflatten

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

s3 = boto3.client('s3', region_name='us-east-1')

# Get the current time for the upcomming update.
now = int(time.mktime(datetime.now().timetuple()))

# Fetch last update time. Use for query.
lastUpdate_file = open("lastUpdate_topic.txt", 'r', encoding="utf-8")
lastUpdate = int(lastUpdate_file.read())
lastUpdate_file.close()
"""
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

# Fetch data from DynamoDB
print("Fetch last documents from 'allScraped'.")
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
sleep(0.1)


for i in result_items:

    # Build file
    if i['fulltext'] != None:
        data = bytes(i['fulltext'], 'utf-8')
    else:
        data = bytes(i['abstract'], 'utf-8')

    # Store data in S3
    s3.put_object(Body = data, Bucket = 'micorr-comprehend-input', Key = str(i['id']))

# Call NLP
comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')

input_s3_url = "s3://micorr-comprehend-input/"
input_doc_format = "ONE_DOC_PER_FILE"
output_s3_url = "s3://micorr-comprehend-output/"
data_access_role_arn = "arn:aws:iam::615606584099:role/service-role/AmazonComprehendServiceRole-inoutS3"
number_of_topics = 100

input_data_config = {"S3Uri": input_s3_url, "InputFormat": input_doc_format}
output_data_config = {"S3Uri": output_s3_url}

start_topics_detection_job_result = comprehend.start_topics_detection_job(JobName="micorr-topicDetection",
                                                                              NumberOfTopics=number_of_topics,
                                                                              InputDataConfig=input_data_config,
                                                                              OutputDataConfig=output_data_config,
                                                                              DataAccessRoleArn=data_access_role_arn)

print('start_topics_detection_job_result: ' + json.dumps(start_topics_detection_job_result))
job_id = start_topics_detection_job_result["JobId"]

print('job_id: ' + job_id)

# Wait for job to finish
call = 0
while True:
    # Refresh status
    describe_topics_detection_job_result = comprehend.describe_topics_detection_job(JobId=job_id)

    if describe_topics_detection_job_result['TopicsDetectionJobProperties']['JobStatus'] == 'COMPLETED':
        print("Detection job complete.")
        break
    else:
        print("Waiting detection job to complete... " + str(call))
        call += 1
        sleep(60) # Time in seconds.
        # Call timeout at 3600 seconds / 1 hour. Match AWS session timeout.
        if call > 60:
            timeout()



# Get archive from S3
#output_pathfile = describe_topics_detection_job_result['TopicsDetectionJobProperties']['OutputDataConfig']['S3Uri']
output_file = "output.tar.gz"

#s3 = boto3.resource('s3', region_name='us-east-1')
#s3.Object('micorr-comprehend-output\\615606584099-TOPICS-e8edba3c9edd6da94b3e2f2570ec48bf\\output\\', 'output.tar.gz').download_file('output.tar.gz')

# Extract tar
tar = tarfile.open(output_file)
tar.extractall()
tar.close()
print("Extracted in Current Directory")

# Parse CSV
df = pd.read_csv('doc-topics.csv', dtype={
            "docname" : str,
            "topic" : str,
            "proportion" : str
        })


results = []

for (docname), bag in df.groupby(["docname"]):
    contents_df = bag.drop(["docname", 'proportion'], axis=1)
    subset = [OrderedDict(row) for i, row in contents_df.iterrows()]
    results.append(OrderedDict([("id", docname),
                                ("topics", subset)]))
for result in results:
    topics = []
    for i in result['topics']:
        topics.append(i['topic'])

    result['fields'] = {}
    result['fields']['topics'] = topics
    del result['topics']

    print(json.dumps(result, indent=4))

updateCloudSearch_file = open("topicFile.json", 'w', encoding="utf-8")
updateCloudSearch_file.write(json.dumps(results))
updateCloudSearch_file.close()

# Fetch all data to reindex
result_items = []

response = allScraped_table.scan(
    IndexName = "last_update-id-index",
    )

result_items.extend(response['Items'])

# Use this bloc for querying
while 'LastEvaluatedKey' in response:
    response = allScraped_table.scan(
        IndexName = "last_update-id-index",
        ExclusiveStartKey = response['LastEvaluatedKey']
    )

    result_items.extend(response['Items'])

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

updateCloudSearch_file = open("docFile.json", 'w', encoding="utf-8")
updateCloudSearch_file.write(json.dumps(batch))
updateCloudSearch_file.close()

# Open index data
with open('docFile.json') as f:
    data = json.load(f)
# Flatten data
doc_df = json_normalize(data)
print("doc_df :\n" + doc_df.head(3).to_string())

# Open topics
with open('topicFile.json') as f:
    data = json.load(f)
# Flatten data
topic_df = json_normalize(data)
print("topic_df :\n" + topic_df.head(3).to_string())

# Add topics to data
results = doc_df.merge(topic_df, how='inner', on='id')
print("results :\n" + results.head(3).to_string())


# Reforme json
docCount = 0
itemsCount = 0
batch = []
result_items = results.to_dict('records')
for r in result_items:
    item = unflatten(r)
    batch.append(item)
    itemsCount += 1
    sleep(0.001) # Wait a bit.

    if itemsCount > 4000 or r == result_items[len(result_items)-1]:
        # Create file
        updateCloudSearch_file = open("updateTopic_" + str(docCount) + ".json", 'w', encoding="utf-8")
        updateCloudSearch_file.write(json.dumps(batch))
        print("Update file n°" + str(docCount) + " complete with " + str(itemsCount) + " documents.")
        updateCloudSearch_file.close()

        docCount += 1
        itemsCount = 0
        batch = []
"""

# Update index
if True:
    print("Start indexing.")
    for doc in range(4):
        #print("Upload file n°" + str(doc) + " with " + str(itemsCount) + " documents.")
        # Call upload
        docEd = 'http://doc-micorr-test-yzjuar4kajhkoii2hgziiq5vxy.us-east-1.cloudsearch.amazonaws.com'
        updateFile = "updateTopic_" + str(doc) + ".json"
        run(["aws", "cloudsearchdomain", "--endpoint-url", docEd, "upload-documents", "--content-type", "application/json", "--documents", updateFile])
else:
    print("Nothing to index.")

# Update last_update
lastUpdate_file = open("lastUpdate_topic.txt", 'w', encoding="utf-8")
lastUpdate_file.write(str(now))
print("Update time set to : " + str(now))
lastUpdate_file.close()
