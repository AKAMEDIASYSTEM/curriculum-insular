#!/usr/bin/env python

# AKA curriculum-insular resolver/worker

import beanstalkc
from pattern.web import URL, plaintext, URLError, MIMETYPE_WEBPAGE, MIMETYPE_PLAINTEXT, HTTPError
from pattern.en import parsetree
from pymongo import MongoClient
import datetime

beanstalk = beanstalkc.Connection(host='localhost', port=14711)
client = MongoClient(tz_aware=True)
db = client.curriculum

while True:
    # take URL and groupID
    # resolve URL into chunks and shove them in 'keywords' with same groupID
    # delete job
    print 'starting worker outer loop'
    job = beanstalk.reserve()  # this is blocking, waits till there's something on the stalk
    pay = job.body.split('|')
    groupID = pay[0]
    url = URL(pay[-1])
    print 'new url, we think', url
    timestamp = datetime.datetime.utcnow()
    try:
        s = url.download(cached=True)
        print url.mimetype
        if (url.mimetype in MIMETYPE_WEBPAGE) or (url.mimetype in MIMETYPE_PLAINTEXT):
            s = plaintext(s)
            '''
            parsetree(string,
                   tokenize = True,         # Split punctuation marks from words?
                       tags = True,         # Parse part-of-speech tags? (NN, JJ, ...)
                     chunks = True,         # Parse chunks? (NP, VP, PNP, ...)
                  relations = False,        # Parse chunk relations? (-SBJ, -OBJ, ...)
                    lemmata = False,        # Parse lemmata? (ate => eat)
                   encoding = 'utf-8'       # Input string encoding.
                     tagset = None)         # Penn Treebank II (default) or UNIVERSAL.
            '''
            parsed = parsetree(s, chunks=True)
            for sentence in parsed:
                # only noun phrases for now but let's pick some good other ones next week
                # seeing ADJP, ADVP, PP and VP mostly tho NP are predominant
                # gen = (the_chunk for the_chunk in sentence.chunks if the_chunk.type=='NP')
                # for chunk in gen:
                for chunk in sentence.chunks:
                    d = db.keywords.update(
                        {'keyword': chunk.string, 'type': chunk.type, 'groupID': groupID},
                        {'$push': {'timestamp': timestamp, 'url': url.string}, '$set': {'latest': timestamp}},
                        upsert=True
                        )
                    # print d
        else:
            'we failed the mimetype test again wtf'
    except HTTPError, e:
        # e = sys.exc_info()[0]
        # print 'URLError on ', url
        print url
        print e
        pass
    except:
        print url
        print 'AKA unhandled exception that we will try to just destroy without halting and catching fire'
    # end of if(isThere < 2)
    job.delete()
    print 'job deleted, we think this was all successful - loop over'
