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

# Set AWS DynamoDB parameters
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
dynamodb_client = boto3.client('dynamodb', region_name='us-east-1')
allScraped_table = dynamodb.Table('allScraped')

s3 = boto3.client('s3', region_name='us-east-1')

# Get the current time for the upcomming update.
now = int(time.mktime(datetime.now().timetuple()))

def timeout():
    raise Exception("Waiting table 'allScraped' timeout.")

def fetchDocuments():
    # Fetch last update time. Use for query.
    lastUpdate_file = open("lastUpdate_topic.txt", 'r', encoding="utf-8")
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

    for i in result_items:

        # Build file
        if i['fulltext'] != None:
            data = bytes(i['fulltext'], 'utf-8')
        else:
            data = bytes(i['abstract'], 'utf-8')

        # Store data in S3
        s3.put_object(Body = data, Bucket = 'micorr-comprehend-input', Key = str(i['id']))
    print('Data stored in AWS S3.')

def callNLP():
    # Call NLP
    comprehend = boto3.client(service_name='comprehend', region_name='us-east-1')

    input_s3_url = "s3://micorr-comprehend-input/"
    input_doc_format = "ONE_DOC_PER_FILE"
    output_s3_url = "s3://micorr-comprehend-output/"
    data_access_role_arn = "arn:aws:iam::615606584099:role/service-role/AmazonComprehendServiceRole-inoutS3"
    number_of_topics = 25

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

### ____ Execution order ____
print('Start fetching documents on DynamoDB.')
fetchDocuments()

print('Call NLP analysis.')
callNLP()

print('Download analysis output and run uploadDocs.py')

# Update last_update
lastUpdate_file = open("lastUpdate_topic.txt", 'w', encoding="utf-8")
lastUpdate_file.write(str(now))
print("Update time set to : " + str(now))
lastUpdate_file.close()
