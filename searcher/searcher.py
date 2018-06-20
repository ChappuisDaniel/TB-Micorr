from __future__ import print_function # Python 2/3 compatibility

import boto3
import json, csv
from subprocess import check_output, call, run

import pandas
from pandas.io.json import json_normalize
from itertools import groupby
from collections import OrderedDict

from stemming.porter2 import stem

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
    """
    distinctTerm = df.term.unique()
    query_file = open("distinctTerm.txt", 'w', encoding="utf-8")
    query_file.write("Distinct term : \n")
    for t in distinctTerm:
        query_file.write(t + "\n")
    query_file.close()
    """
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

    topicFilter = 0.02

    # Select topics on matching term
    topics = []
    nearTerms = []
    for term in request.split():
        # Search for raw term
        topics.append(ttw.loc[ttw['term'] == term])
        # Search for stemmed term
        stemmedTerm = stem(term)
        topics.append(ttw.loc[ttw['term'] == stemmedTerm])

        # Seems to wide
        #topics.append(ttw.loc[ttw['term'].str.contains(stemmedTerm)])

        nearTerms.append("(near+distance%3D" + str(nearDistance) + "+'" + term + "')")


    # Get the higher topic
    queryTopics = []
    for topic in topics:
        if not topic.empty:
            #print("Topic : \n" + topic.to_string())

            # Select a list of higher topics
            higherTopics = topic.loc[topic.weight > topicFilter]
            #print("Filtred topic : \n" + higherTopics.to_string())

            if higherTopics.empty:
                # Get the best topic
                bestTopic = topic.loc[[topic['weight'].idxmax()]]
                # Jsonify
                best_topic = bestTopic.to_dict('records')[0]
                #print("Best topic : \n" + json.dumps(best_topic, indent=4))
                queryTopics.append("(term+field%3Dtopics+boost%3D" + str(topicBoost) + "+'" + best_topic['topic'] + "')")

            for filtredTopic in higherTopics.to_dict('records') :
                queryTopics.append("(term+field%3Dtopics+boost%3D" + str(topicBoost) + "+'" + filtredTopic['topic'] + "')")

            #topicsAnalysis_file.write("'"+request+"'\nTopic : \n" + topic.to_string() + "\nBest topic : \n" + json.dumps(best_topic, indent=4)+"\n\n")

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
#topicsAnalysis_file = open("topicsAnalysis.txt", 'w', encoding="utf-8")
for request in userSearchTerm:
    createQuery(request=request)
query_file.close()
#topicsAnalysis_file.close()
