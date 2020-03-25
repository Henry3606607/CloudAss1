
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


def user_key(user_id):
    return ndb.Key('id', user_id)


class User(ndb.Model):
    id = ndb.KeyProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    password = ndb.IntegerProperty(indexed=False)

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

class MainPage(MyBaseHandler):

    def get(self):
        login_failed = self.request.get('login_fail',
                                          False)
        self.session['user'] = None
        template_values = {
            'login_failed': login_failed
        }

        template = JINJA_ENVIRONMENT.get_template('login.html')
        self.response.write(template.render(template_values))

class Login(MyBaseHandler):

    def post(self):
        user_query = User.query().filter(ndb.KeyProperty('id') == user_key(self.request.get('username')))

        user = user_query.fetch(1)

        login_failed = True
        found_user = None
        if len(user) == 1:
            found_user = user[0]
            if self.request.get('password').isdigit():
                if found_user.password == int(self.request.get('password')):
                    login_failed = False


        template_values = {
            'response': user
        }


        if login_failed:
            self.redirect('/?' + urllib.urlencode({'login_fail': found_user}))
        else:
            self.session['user'] = found_user
            self.redirect('/main')

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

        template = JINJA_ENVIRONMENT.get_template('name.html')
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
        params = {
            'user': self.session.get('user', 'testfailed'),
            'error': self.request.get('error')
        }

        template = JINJA_ENVIRONMENT.get_template('password.html')
        self.response.write(template.render(params))

class ChangePassword(MyBaseHandler):

    def post(self):
        test = {
            'user': self.session.get('user', 'testfailed')
        }
        oldPassword = self.request.get('oldPassword')
        newPassword = self.request.get('newPassword')
        if oldPassword and newPassword:
            if oldPassword.isdigit() and newPassword.isdigit():
                new_user = test['user'].key.get()
                if new_user.password == int(oldPassword):
                    new_user.password = int(newPassword)
                    new_user.put()
                    self.redirect('/')
                    return

        query_params = {'error': True}
        self.redirect('/password?' + urllib.urlencode(query_params))

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': 'my-super-secret-key',
}

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/login', Login),
    ('/main', Main),
    ('/password', Password),
    ('/change-password', ChangePassword),
    ('/name', Name),
    ('/change-username', ChangeUsername),
], config=config, debug=True)
