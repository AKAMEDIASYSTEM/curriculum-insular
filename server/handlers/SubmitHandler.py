#!/usr/bin/env python
# curriculum-insular
# experiments with google physical-web mdns broadcast

from handlers.BaseHandler import BaseHandler
from ResponseObject import ResponseObject
import datetime
import beanstalkc


class SubmitHandler(BaseHandler):
    """json submission to curriculum-insular store"""

    def post(self):
        beanstalk = beanstalkc.Connection(host='localhost', port=14711)
        print 'inside curriculum-insular SubmitHandler'
        if self.isAuth():
            print 'isAuth was successful'
            db = self.settings['db']
            url = self.get_argument('url')
            groupID = self.get_argument('groupID')
            timestamp = datetime.datetime.utcnow()
            print 'hit the insular SubmitHandler endpoint with url=', url
            # search pages collection for this url and groupID combo
            # if present already, do nothing (pages coll has TTL of 10 mins)
            # if absent, add url to pages AND do lang processing
            isThere = db.pages.find({'url': url, 'groupID': groupID}).count()
            print 'isThere is ', isThere
            if isThere < 1:
                # populate Pages collection
                print 'adding the url because we havent seen it before'
                # hey we dont need timestamps in this anymore, do we?
                # take them out if you decide TTL is sufficient?
                db.pages.update(
                    {'url': url, 'groupID': groupID},
                    {'$push': {'timestamp': timestamp}, '$set': {'latest': timestamp}},
                    upsert=True
                    )
                combo = '|'.join((groupID, str(url)))
                print combo
                combo = str(combo)
                beanstalk.put(combo)
            else:
                print 'we have already seen this groupID and url recently, not queueing it', url
            self.response = ResponseObject('200', 'Success')
        else:
            print 'isAuth returned False'
            self.response = ResponseObject('500', 'Error - authentication failed')
        self.write_response()
        self.finish()
