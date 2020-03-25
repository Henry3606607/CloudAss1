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
from webapp2_extras import sessions


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
class User(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    id = ndb.KeyProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    password = ndb.IntegerProperty(indexed=False)
# [END greeting]

class MyBaseHandler(webapp2.RequestHandler):
    #base handlers sourced from: https://stackoverflow.com/questions/18286294/webapp2-get-session-value-from-basehandler-method?rq=1
    def dispatch(self):
        # get a session store for this request
        self.session_store = sessions.get_store(request=self.request)
        try:
            # dispatch the request
            webapp2.RequestHandler.dispatch(self)
        finally:
            # save all sessions
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # returns a session using the backend more suitable for your app
        backend = "memcache" # use app engine's memcache
        return self.session_store.get_session(backend=backend)

# [START main_page]
class MainPage(MyBaseHandler):

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
class Login(MyBaseHandler):

    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        user_query = User.query().filter(ndb.KeyProperty('id') == user_key(self.request.get('username')))
        #user_query = User.query().key_filter(user_key(self.request.get('username')))
        #user_query = User.query(User.password = self.request.get('password'))
        #user_query = User.query()

        user = user_query.fetch(1)

        login_failed = True
        found_user = None
        if len(user) == 1:
            found_user = user[0]
            #TODO come back here and check for int
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
            self.session['user'] = found_user
            self.redirect('/main')
# [END guestbook]

class Main(MyBaseHandler):

    def get(self):
        test = {
            'user': self.session.get('user', 'testfailed')
        }

        template = JINJA_ENVIRONMENT.get_template('main.html')
        self.response.write(template.render(test))

class Name(MyBaseHandler):

    def get(self):
        params = {
            'user': self.session.get('user', 'testfailed'),
            'error': self.request.get('error')
        }

        template = JINJA_ENVIRONMENT.get_template('changeUsername.html')
        self.response.write(template.render(params))


class ChangeUsername(MyBaseHandler):

    def post(self):
        test = {
            'user': self.session.get('user', 'testfailed')
        }
        if self.request.get('username'):
            new_user = test['user'].key.get()
            new_user.name = self.request.get('username')
            new_user.put()

            self.session['user'] = new_user
            self.redirect('/main')
        else:
            query_params = {'error': True}
            self.redirect('/name?' + urllib.urlencode(query_params))

class Password(MyBaseHandler):

    def get(self):
        test = {
            'user': self.session.get('user', 'testfailed')
        }

        template = JINJA_ENVIRONMENT.get_template('changePassword.html')
        self.response.write(template.render(test))

class ChangePassword(MyBaseHandler):

    def post(self):
        test = {
            'user': self.session.get('user', 'testfailed')
        }
        if self.request.get('username'):
            new_user = test['user'].key.get()
            new_user.name = self.request.get('username')
            new_user.put()

            self.session['user'] = new_user
            self.redirect('/main')
        else:
            query_params = {'error': True}
            self.redirect('/name?' + urllib.urlencode(query_params))

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}

# [START app]
app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', Login),
    ('/main', Main),
    ('/password', Password),
    ('/change-password', ChangePassword),
    ('/name', Name),
    ('/change-username', ChangeUsername),
], config=config, debug=True)
# [END app]
