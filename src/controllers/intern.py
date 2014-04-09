"""
Controller for website administration stuff.
"""

import datetime
import json
import logging
import sys
import webapp2

from authentication import auth
from models import models, webapputils, report_results
from google.appengine.api import mail, taskqueue

COMMANDERS = ['wa1', 'dan1']

class CommandCenterHandler(webapp2.RequestHandler):

    def get(self):
        voter = auth.get_voter(self)
        if voter.net_id not in COMMANDERS:
            return webapputils.render_template('/templates/message', {
                'status': 'Not Authorized',
                'msg': "You're not authorized to enter the command center"
            })

        organizations = []
        # Aggregate all information about organizations
        for org in models.Organization.all():
            organizations.append({
                'name': org.name,
                'electionCount': org.elections.count(),
                'adminCount': org.organization_admins.count(),
                'voteCount': sum([elec.voted_count for elec in org.elections])
            })


        # get 20 elections that have not ended, sorted by starting time
        elections = [e.to_json(True) for e in models.Election.all().filter(
            'end >', datetime.datetime.now()).order('end').order(
                'start').run(limit=20)]
        page_data = {
            "organizations": organizations,
            "elections": elections
        }

        return webapputils.render_page(self, '/intern/command-center', page_data)

    def post(self):
        methods = {
            'create_organization': self.create_organization,
            'add_admin': self.add_admin
        }
        data = json.loads(self.request.get('data'))
        voter = auth.get_voter(self)
        if voter.net_id not in COMMANDERS:
            return  # hacker
        out = methods[data['method']](data)

    def create_organization(self, data):
        org = models.Organization(
            name=data['name'],
            description=data['description'],
            website=data['website']
        )
        org.put()
        webapputils.respond(self, 'OK', 'Done')

    def add_admin(self, data):
        org = models.Organization.get(data['organization'])
        voter = get_voter(data['net_id'], create=True)
        org_admin = models.put_admin(voter, data['email'], org)
        if org_admin:
            webapputils.respond(self, 'OK', 'Done')
        else:
            webapputils.respond(self, 'ERROR', "Couldn't create admin")

class JobsHandler(webapp2.RequestHandler):
    """Large processing tasks that should be executed on the server side, instead
    of the remote api shell for performance and cost reasons. If you are running
    a task on the remote api shell that will load thousands of Datastore objects
    it will be extremely slow and very expensive so write the code here instead
    and run it on the server by accessing the endpoint ONCE."""

    def get(self):
        voter = auth.get_voter(self)
        if voter.net_id not in COMMANDERS:
            return webapputils.render_template('/templates/message', {
                'status': 'Not Authorized',
                'msg': "You're not authorized to enter the command center"
            })

        jobs = models.ProcessingJob.gql("ORDER BY started DESC LIMIT 20")
        ready = {
            "name": "MartelDeleteCampusWideElection",
            "description": "Deletes Campus Wide Positions Election for Martel Its Incomplete"
        }

        page_data = {
            "jobs": jobs,
            "ready": ready
        }

        return webapputils.render_page(self, '/intern/jobs', page_data)

    def post(self):

        job = models.ProcessingJob(
            name=self.request.get('ready_name'),
            description=self.request.get('ready_description'),
            status='running'
        )

        job.put()

        retry_options = taskqueue.TaskRetryOptions(task_retry_limit=0)
        taskqueue.add(
            name=job.name,
            url='/intern/jobs-taskqueue',
            params={
                'job_key': str(job.key())
            },
            retry_options=retry_options
        )

        self.response.write(json.dumps(job.to_json()))


class JobsTaskQueueHandler(webapp2.RequestHandler):

    def post(self):
        job = models.ProcessingJob.get(self.request.get('job_key'))

        try:
            description = "Deletes Campus Wide Positions Election for Martel Its Incomplete"
            # Assertion here to ensure that the developer is running the right
            # task
            assert(job.description == description)

            ### Processing begin ###

            martel = models.get_organization("Martel College")
            campus_wide = models.Election.gql("WHERE name=:1 AND organization=:2",
                "Campus Wide Positions", martel).get()
            models.delete_election(campus_wide)

            ### Processing end ###

            job.status = "complete"
        finally:
            if job.status != "complete":
                job.status = "failed"
            job.ended = datetime.datetime.now()
            job.put()


app = webapp2.WSGIApplication([
    ('/intern/command-center', CommandCenterHandler),
    ('/intern/jobs', JobsHandler),
    ('/intern/jobs-taskqueue', JobsTaskQueueHandler)
], debug=True)
