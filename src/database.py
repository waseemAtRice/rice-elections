"""
Database for the app.
"""

__author__ = 'Waseem Ahmad (waseem@rice.edu)'

import logging

from datetime import datetime
from google.appengine.ext import db


class Organization(db.Model):
    """
    An organization that uses this application to host elections.
    Organizations are tied to individual Elections and OrganizationPositions.
    """
    name = db.StringProperty()
    description = db.TextProperty()
    website = db.StringProperty()

def get_organization(name):
    """
    Returns the organization the election data is referring to.
    
    Args:
        name: The name of the organization.
    
    Returns:
        Organization from database. None if it doesn't exist.
    """
    temp_hard_code = True
    
    if not name:
        if temp_hard_code:
            name = 'Brown College'
        else:
            return None
    
    query_result = db.GqlQuery('SELECT * FROM Organization WHERE name=:1 LIMIT 1', name).run()
    for organization in query_result:
        return organization
    
    # Create Brown College organization
    if temp_hard_code:
        brown = Organization()
        brown.name = name
        brown.description = 'The best residential college.'
        brown.website = 'http://brown.rice.edu'
        brown.put()
        return brown
    
    return None

class Election(db.Model):
    """
    An election that users may vote for.
    """
    name = db.StringProperty()
    start = db.DateTimeProperty()       # Time when voting begins
    end = db.DateTimeProperty()         # Time when voting ends
    organization = Organization()       # The organization holding the election

def put_election(name, start, end, organization):
    """
    Creates and stores an election in the database.
    
    Args:
        name: election name.
        start: start time in time since epoch
        end: end time in time since epoch
        organization: the election Organization
        
    Returns:
        election: the Election object stored in the database
    """
    for arg in [name, start, end, organization]:
        if not arg:
            raise Exception('One or more args missing')
    logging.info('Storing new election: %s, start: %s, end: %s, organization: %s',
                 name, start, end, organization.name)
    election = Election()
    election.name = name
    election.start = datetime.fromtimestamp(start)
    election.end = datetime.fromtimestamp(end)
    election.organization = organization
    election.put()
    logging.info('Election stored.')
    return election


class Voter(db.Model):
    """
    A voter that uses the application.
    """
    net_id = db.StringProperty()
    

class EligibleVoter(db.Model):
    """
    An entity that represents an election that an individual voter is eligible to vote for.
    """
    voter = Voter()
    election = Election()
    
def add_eligible_voters(election, net_id_list):
    """
    Adds the specified people as eligible voters for the election provided. Creates and stores a
    Voter entry for NetIDs who currently do not have a corresponding voter.
    
    Args:
        election: Election object to add eligible voters for.
        net_id_list: List of NetID strings
    """
    for net_id in net_id_list:
        voter = get_voter(net_id, create=True)
        eligible_voter = EligibleVoter()
        eligible_voter.voter = voter
        eligible_voter.election = election
        eligible_voter.put()

def get_voter(net_id, create=False):
    """
    Returns the Voter entry for the NetID specified.
    
    Args:
        net_id: NetID of the Voter.
        create(optional): Creates and stores a Voter entry if one doesn't exist.
    
    Returns:
        voter: The Voter entry corresponding to net_id, None if one doesn't exist and create is False.
    """
    query_result = db.GqlQuery('SELECT * FROM Voter WHERE net_id=:1 LIMIT 1', net_id).run()
    for voter in query_result:
        return voter
    
    if create:
        voter = Voter()
        voter.net_id = net_id
        voter.put()
        logging.info('Voter with NetID: %s created and stored.', net_id)
        return voter
    
    return None

def get_elections_for_voter(voter):
    """
    Returns the Elections the Voter is eligible for voting in.
    
    Args:
        voter: The Voter.
    
    Returns:
        elections: A list of Election entries the voter is eligible to vote in.
    """
    query = db.GqlQuery('SELECT * FROM EligibleVoter WHERE voter=:1', voter)
    elections = []
    for eligible_voter in query:
        elections.append(eligible_voter.election)
    logging.info(elections)
    return elections