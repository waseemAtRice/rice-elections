"""
Back-end for the Organization Panel.
"""

__author__ = 'Waseem Ahmad <waseem@rice.edu>'

import database
import json
import logging
import webapp2

from authentication import require_login, get_voter
from datetime import datetime, timedelta
from google.appengine.api import taskqueue
from google.appengine.ext import db
from main import render_page

PAGE_NAME = '/organization-panel'
MSG_NOT_AUTHORIZED = ('We\'re sorry, you\'re not an organization administrator. Please contact the website administration '
                     'if you are interested in conducting elections for your organization.')

class AdminHandler(webapp2.RequestHandler):

    def get(self):
        # Authenticate user
        voter = get_voter()
        if not voter:
            require_login(self)
        status = database.get_admin_status(voter)
        if not status:
            render_page(self, '/message', {'status': 'Not Authorized', 'msg': MSG_NOT_AUTHORIZED})
            return

        # Get organization information
        admin = database.Admin.gql('WHERE voter=:1', voter).get()
        org_admin = database.OrganizationAdmin.gql('WHERE admin=:1',
                                                    admin).get()
        org = org_admin.organization

        # Construct page information
        page_data = {}
        page_data['organization'] = org
        page_data['admins'] = self.admin_list(org)
        page_data['elections'] = [elec.to_json() for elec in org.elections]

        render_page(self, PAGE_NAME, page_data)

    def post(self):
        # Authenticate user
        voter = get_voter()
        if not voter:
            self.respond('ERROR', MSG_NOT_AUTHORIZED)
            return
        status = database.get_admin_status(voter)
        if not status:
            self.respond('ERROR', MSG_NOT_AUTHORIZED)
            return

        # Get method and data
        logging.info('Received call')
        data = json.loads(self.request.get('data'))
        methods = {'update_profile': self.update_profile}
        methods[data['method']](data['data'])

    def respond(self, status, message):
        """
        Sends a response to the front-end.

        Args:
            status: response status
            message: response message
        """
        self.response.write(json.dumps({'status': status, 'msg': message}))

    def update_profile(self, data):
        """
        Updates the organization profile.
        """
        logging.info('Updating profile')
        org_id = data['id']
        org = database.Organization.get(org_id)
        assert database.get_admin_status(get_voter(), org)
        for field in ['name', 'description', 'website']:
            setattr(org, field, data[field].strip())
        org.put()
        self.respond('OK', 'Updated')

    @staticmethod
    def admin_list(organization):
        admins = []
        for organization_admin in organization.organization_admins:
            admin = {}
            admin['name'] = organization_admin.admin.name
            admin['email'] = organization_admin.admin.email
            admins.append(admin)
        return admins

app = webapp2.WSGIApplication([
        ('/organization-panel', AdminHandler)
], debug=True)