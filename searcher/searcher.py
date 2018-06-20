from __future__ import print_function # Python 2/3 compatibility

import boto3
import json, csv
from subprocess import check_output, call, run

import pandas
from pandas.io.json import json_normalize
from itertools import groupby
from collections import OrderedDict

userSearchTerm = [
    'corrosion active',
    'localised corrosion',
    'efflorescence',
    'original surface',
    'limit of the original surface',
    'markers of the original surface',
    'cracking',
    'mineralised metal',
    'patina',
    'filiform corrosion',
    'cold working',
    'hot working',
    'zinc pest',
    'surface hardening',
    'heterogeneous tarnishing',
    'metal etching',
    'soldering',
    'paint layers',
    'surface enrichment',
    'non corroded metal'
]

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


def createQuery(request):
    """
    Search and add topic to the query based upon the terms given.
    """

    # Initialize topic-term-weight
    ttw = parseTopicTerm()

    nearDistance = 3
    facetteSize = 5
    topicBoost = 2

    # Select topics on matching term
    topics = []
    nearTerms = []
    for term in request.split():
        topics.append(ttw.loc[ttw['term'] == term])

        nearTerms.append("(near+distance%3D" + str(nearDistance) + "+'" + term + "')")


    # Get the higher topic
    queryTopics = []
    for topic in topics:
        if not topic.empty:
            print("Topic : \n" + topic.head(5).to_string())

            # Select higher
            bestTopic = topic.loc[[topic['weight'].idxmax()]]
            #print("Topic : " + bestTopic.head(5).to_string())

            # Jsonify
            best_topic = bestTopic.to_dict('records')[0]
            print("Best topic : \n" + json.dumps(best_topic, indent=4))

            queryTopics.append("(term+field%3Dtopics+boost%3D" + str(topicBoost) + "+'" + best_topic['topic'] + "')")

    str_nearTerms = ""
    for i in nearTerms:
        str_nearTerms += i

    str_queryTopics = ""
    for i in queryTopics:
        str_queryTopics += i
    # Build query
    query = "/2013-01-01/search?q=(or+" + str_queryTopics + str_nearTerms + ")&q.parser=structured&facet.topics={sort:\"bucket\", size:" + str(facetteSize) + "}"

    query_file.write(query + "\n")


query_file = open("query.txt", 'w', encoding="utf-8")
for request in userSearchTerm:
    createQuery(request=request)
query_file.close()
