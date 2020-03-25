#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START imports]
import os
import urllib
import array

from google.appengine.api import app_identity
from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)
# [END imports]

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'


# We set a parent key on the 'Greetings' to ensure that they are all
# in the same entity group. Queries across the single entity group
# will be consistent. However, the write rate should be limited to
# ~1/second.

def user_key(user_id):
    """Constructs a Datastore key for a Guestbook entity.

    We use guestbook_name as the key.
    """
    return ndb.Key('id', user_id)


# [START greeting]
class Test(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    id = ndb.KeyProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    password = ndb.IntegerProperty(indexed=False)
# [END greeting]


# [START main_page]
class MainPage(webapp2.RequestHandler):

    def get(self):
        login_failed = self.request.get('login_fail',
                                          False)

        template_values = {
            'login_failed': login_failed
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))
# [END main_page]


# [START guestbook]
class Login(webapp2.RequestHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        user_query = Test.query().filter(ndb.KeyProperty('id') == user_key(self.request.get('username')))
        #user_query = Test.query().key_filter(user_key(self.request.get('username')))
        #user_query = Test.query(Test.password = self.request.get('password'))
        #user_query = Test.query()

        user = user_query.fetch(1)

        login_failed = True
        found_user = None
        if len(user) == 1:
            found_user = user[0]
            if found_user.password == int(self.request.get('password')):
                login_failed = False


        #login_request = User(parent=user_key(self.request.get('username'))

        #login_request.username = self.request.get('username')
        #login_request.password = self.request.get('password')
        #login_request.put()

        template_values = {
            'response': user
        }

      #  template = JINJA_ENVIRONMENT.get_template('index.html')
       # self.response.write(template.render(template_values))

        if login_failed:
            self.redirect('/?' + urllib.urlencode({'login_fail': found_user}))
        else:
            self.redirect('/main?' + urllib.urlencode({'username': self.request.get('username')}))
# [END guestbook]


# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', Login),
], debug=True)
# [END app]
