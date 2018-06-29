from __future__ import print_function # Python 2/3 compatibility

import json, csv
import requests

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
queriesList = []
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
    termBoost = 2
    topicBoost = 1.5

    topicFilter = 0.0

    # Select topics on matching term
    topics = []
    nearTerms = []
    for term in request.split():
        # Search for raw term
        topics.append(ttw.loc[ttw['term'] == term])
        # Search for stemmed term
        stemmedTerm = stem(term)
        topics.append(ttw.loc[ttw['term'] == stemmedTerm])

        #nearTerms.append("(near+distance%3D" + str(nearDistance) + "+'" + term + "')")
        nearTerms.append("(near+distance%3D" + str(nearDistance) + "+boost%3D" + str(termBoost) + "+'" + term + "')")

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
                #queryTopics.append("(term+field%3Dtopics+'" + best_topic['topic'] + "')")
                queryTopics.append("(term+field%3Dtopics+boost%3D" + str(topicBoost) + "+'" + best_topic['topic'] + "')")

            for filtredTopic in higherTopics.to_dict('records') :
                #queryTopics.append("(term+field%3Dtopics+'" + filtredTopic['topic'] + "')")
                queryTopics.append("(term+field%3Dtopics+boost%3D" + str(topicBoost) + "+'" + filtredTopic['topic'] + "')")

            #topicsAnalysis_file.write("'"+request+"'\nTopic : \n" + topic.to_string() + "\nBest topic : \n" + json.dumps(best_topic, indent=4)+"\n\n")

    str_nearTerms = ""
    for i in nearTerms:
        str_nearTerms += i

    str_queryTopics = ""
    for i in queryTopics:
        str_queryTopics += i
    # Q1 : Only search words without boost
    #query = "/2013-01-01/search?q=(and" + str_nearTerms + ")&q.parser=structured&return=title,abstract,article_type,topics&size=30"

    # Q2 : With topics without boost
    # Q3 : With topics and boost
    query = "/2013-01-01/search?q=(or+" + str_queryTopics + "(and" + str_nearTerms + "))&q.parser=structured&return=title,abstract,article_type,topics&size=30"

    testQuery(query=query, request=request)

    query_file.write(query + "\n")
    queriesList.append(query)


def testQuery(query, request):
    r = requests.get('http://search-micorr-test-yzjuar4kajhkoii2hgziiq5vxy.us-east-1.cloudsearch.amazonaws.com' + query)

    print('\n Status : '+ str(r.status_code))
    #print('\n Json : '+ json.dumps(r.json()))

    searchResults = r.json()['hits']['hit']

    order = 1
    for i in searchResults:
        if not 'topics' in i['fields']:
            i['fields']['topics'] = ""

        i['fields']['id'] = i['id']
        i['fields']['order'] = order
        order += 1

    # open a file for writing
    response = open("results/csv/"+ request +".csv", 'w', encoding="utf-8")

    # create the csv writer object
    csvwriter = csv.writer(response)

    count = 0
    for hit in searchResults:
        if count == 0:
            header = hit['fields'].keys()
            csvwriter.writerow(header)
            count = 1

        csvwriter.writerow(hit['fields'].values())

    response.close()

###________Main_________________________________________________________________
query_file = open("query.txt", 'w', encoding="utf-8")
#topicsAnalysis_file = open("topicsAnalysis.txt", 'w', encoding="utf-8")
for request in userSearchTerm:
    createQuery(request=request)
query_file.close()
#topicsAnalysis_file.close()
