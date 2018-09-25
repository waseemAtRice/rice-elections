"""
Application specific authentication module.
"""

__author__ = 'Waseem Ahmad <waseem@rice.edu>'


import logging
import re
import urllib
import webapp2

from gaesessions import get_current_session
from models import models
from models.webapputils import render_page

CAS_SERVER  = "https://netid.rice.edu"


class LoginResponseHandler(webapp2.RequestHandler):
    """Receive the response from CAS after the user authentication."""

    def get(self):
        ticket = self.request.get('ticket')

        if not ticket:
            render_page(self, '/templates/message', {'status': 'Error', 'msg': 'Ticket not specified.'})
            return

        net_id = self.validate_cas_2()
        if not net_id:
            render_page(self, '/templates/message', {'status': 'Error', 'msg': 'Invalid ticket. Credentials not verified.'})
            return

        # Close any active session the user has since credentials have been freshly verified.
        session = get_current_session()
        if session.is_active():
            session.terminate()

        # Get the user's record
        voter = models.get_voter(net_id, create=True)

        # Start a session for the user
        session['net_id'] = voter.net_id

        destination_url = str(self.request.get('destination'))
        if not destination_url:
            render_page(self, '/templates/message', {'status': 'Error', 'msg': 'User authenticated. However, no destination '
                              'url is provided.'})
            return

        logging.info('Redirecting to %s', destination_url)
        self.redirect(destination_url)

    def validate_cas_2(self):
        """
        Validate the given ticket using CAS 2.0 protocol.

        Returns:
            net_id {String}: the id of the user. None if ticket invalid.
        """
        ticket = self.request.get('ticket')
        service_url = self.remove_parameter_from_url(self.request.url, 'ticket')        # Strip ticket parameter
        cas_validate = CAS_SERVER + '/cas/serviceValidate?ticket=' + ticket + '&service=' + service_url

        # Ask CAS server whether this ticket is valid
        f_validate = urllib.urlopen(cas_validate)

        # Get the first line - should be yes or no
        response = f_validate.read()
        net_id = self.parse_tag(response, 'cas:user')
        if not net_id:
            logging.warning('Invalid ticket.\nResponse: %s\nService-Url: %s\nServer-Url: %s', 
                            response, service_url, cas_validate)
            return None

        logging.info('Ticket validated for %s', net_id)
        return net_id

    @staticmethod
    def parse_tag(string, tag):
        """
        Used for parsing XML. Searches the string for first occurrence of <tag>...</tag>.

        Returns:
            The trimmed text between tags. "" if tag is not found.
        """
        tag1_pos1 = string.find("<" + tag)
        #  No tag found, return empty string.
        if tag1_pos1==-1: return ""
        tag1_pos2 = string.find(">",tag1_pos1)
        if tag1_pos2==-1: return ""
        tag2_pos1 = string.find("</" + tag,tag1_pos2)
        if tag2_pos1==-1: return ""
        return string[tag1_pos2+1:tag2_pos1].strip()

    @staticmethod
    def remove_parameter_from_url(url, parameter):
        """
        Removes the specified parameter from the url. Returns url as is if parameter doesn't exist.

        Args:
            url {String}: input url
            parameter {String}: parameter to remove.
        Returns:
            {String}: url with ticket parameter removed.
        """
        return re.sub('&%s(=[^&]*)?|%s(=[^&]*)?&?' % (parameter, parameter), '', url)


class LogoutHandler(webapp2.RequestHandler):
    def get(self):
        """Logs out the user from CAS."""
        app_url = self.request.headers.get('host', 'no host')    # URL of the app itself
        service_url = 'https://%s/authenticate/logout-response' % app_url
        self.redirect(CAS_SERVER + '/cas/logout?service=' + service_url)


class LogoutResponseHandler(webapp2.RequestHandler):
    def get(self):
        """Logs out the user."""
        session = get_current_session()
        if session.has_key('net_id'):
            session.terminate()
            render_page(self, '/templates/message', {'status': 'Logged Out', 'msg': 'You\'ve been logged out. See you again soon!'})
        else:
            render_page(self, '/templates/message', {'status': 'Silly', 'msg': 'You weren\'t logged in.'})

def redirect_to_cas(request_handler):
    """
    Redirects client to CAS server for credentials verification.
    """

def require_login(request_handler):
    """
    Requires the user to be logged in through NetID authentication.

    Args:
        request_handler: webapp2 request handler of the user request
    """
    destination_url = request_handler.request.url
    app_url = request_handler.request.headers.get('host', 'no host')    # URL of the app itself
    service_url = 'https://%s/authenticate/login-response' % app_url
    cas_url = CAS_SERVER + '/cas/login?service=' + service_url + '?destination=' + destination_url
    request_handler.redirect(cas_url, abort=True)

def get_voter(handler=None):
    """
    Returns the voter from user session.

    Args:
        handler {webapp2.RequestHandler}: Redirects the user to login if the
            user is not logged in. Note: Redirects only work for GET requests.

    Returns:
        voter: the Voter if authenticated. None otherwise.
    """
    session = get_current_session()
    if session.has_key('net_id'):
        return models.get_voter(session['net_id'])
    elif handler:
        require_login(handler)
    else:
        return None

def set_organizations(organizations):
    """
    Sets the specified organization for reference for the logged in admin.

    Args:
        organization {List <Organization>}: the organizations to set.
    """
    session = get_current_session()
    session['_organizations'] = [str(organization.key()) for organization in organizations]

def set_active_organization(organization):
    """
    Sets the active organization of the current logged in admin for reference.

    Args:
        organization {Organization}: the organization to set.
    """
    session = get_current_session()
    session['_active_organization'] = str(organization.key())

def get_organization():
    """
    Gets the organization from the admin session.

    Returns:
        organization {Organization}: the Organization that the admin is working
            with.
    """
    session = get_current_session()
    if session.has_key('_organization'):
        return models.Organization.get(session['_organization'])
    else:
        return None

def get_active_organization():
    """
    Gets the organization from the admin session.

    Returns:
        organization {Organization}: the Organization that the admin is working
            with.
    """
    session = get_current_session()
    if session.has_key('_active_organization'):
        return models.Organization.get(session['_active_organization'])
    else:
        return None

def set_election(election):
    """
    Sets the specified election for reference for the logged in admin.

    Args:
        election {Election}: the election to set.
    """
    session = get_current_session()
    session['_election'] = str(election.key())

def clear_election():
    """
    Clears the election from admin session data.
    """
    session = get_current_session()
    if session.has_key('_election'):
        del session['_election']

def get_election():
    """
    Gets the election from the admin session.

    Returns:
        election {Election}: the Election the the admin is working with.
    """
    session = get_current_session()
    if session.has_key('_election'):
        return models.Election.get(session['_election'])
    else:
        return None
