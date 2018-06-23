from __future__ import print_function # Python 2/3 compatibility
import sys
import boto3
import json, csv
from subprocess import check_output, call, run
import requests

import pandas
from pandas.io.json import json_normalize
from itertools import groupby
from collections import OrderedDict

from stemming.porter2 import stem

def parseTopicTerm():
    """
    Parse CSV tu create a searchable table.
    """
    df = pandas.read_csv('topic-terms.csv', dtype={
                "topic" : str,
                "term" : str,
                "weight" : float
            })
    return df

def predictTerm(input):
    # Initialize topic-term-weight
    ttw = parseTopicTerm()

    topicFilter = 0.015

    # Select topics on matching term
    topics = []
    for term in input.split():
        # Search for raw term
        topics.append(ttw.loc[ttw['term'] == term])
        # Search for stemmed term
        stemmedTerm = stem(term)
        topics.append(ttw.loc[ttw['term'] == stemmedTerm])
    #print(topics)

    # Get suggestion for topics
    suggestionTopics = []
    for topic in topics:
        if not topic.empty:
            # Select a list of higher topics
            higherTopics = topic.loc[topic.weight > topicFilter]

            if higherTopics.empty:
                # Get the best topic in any higher.
                filtredTopics = topic.loc[[topic['weight'].idxmax()]]

            # Fetch terms for topics
            for filtredTopic in higherTopics.to_dict('records'):
                suggestionTopics.append(filtredTopic['topic'])

    suggestions = []
    for topic in suggestionTopics:
        df = ttw.loc[ttw['topic'] == topic]
        #suggestions.append(df.to_dict('record')[1]['term'])
        df = df.loc[[df['weight'].idxmax()]]
        suggestions.append(df.to_dict('record')[0]['term'])
    return suggestions


s = ''
for t in range(1, len(sys.argv)):
    s += sys.argv[t] + " "
print(s)
print(predictTerm(s))
