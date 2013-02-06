#!/usr/bin/env python

__author__ = "Aleksey Korzun"
__email__ = "al.ko@webfoundation.net"
__credits__ = ["Aleksey Korzun", "Elliot Carlson"]
__license__ = "GPL"
__version__ = "1.0"

import os
import sys
import time
import requests
import argparse

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)

"""
Election class
"""


class Election:
    # Domain that supports API methods
    DOMAIN = 'http://www.reddit.com'

    """
    Initializes class
    """
    def __init__(self):
        self.client = None
        self.candidate = None
        self.comments = []
        self.voters = {}

    """
    Sets candidate that should be voted on by voters

        Arguments:

            candidate
                Username of Reddit account you wish to cast votes on
    """
    def setCandidate(self, candidate):
        self.candidate = candidate

    """
    Adds a new voter to the system

        Arguments:

            username
                Username of your voter

            password
                Password of your voter
    """
    def addVoter(self, username, password):
        self.voters[username] = password

    """
    Retrieve saved id of the last comment we voted on
    """
    def lastCommentId(self):
        try:
            handle = open(os.path.join(__location__, '.last_id'), 'r')
            id = handle.read().rstrip()
            handle.close()
        except IOError:
            id = None

        return id

    """
    Update (or create) last comment id we voted on

        Arguments:

            id
                Identifier of the last comment we saw
    """
    def setLastCommentId(self, id):
        handle = open(os.path.join(__location__, '.last_id'), 'w')
        handle.write(id)
        handle.close()

    """
    This method retrieves all of the comments that were yet to be voted on
    for internal storage.

    Upon successful retrieval method will begin voting using voters you setup
    """
    def begin(self):
        # Make sure election is properly setup
        try:
            if (self.candidate is None):
                raise Exception(
                    'A valid candidate must be provided prior to election'
                )
            elif (len(self.voters) == 0):
                raise Exception(
                    'Voters must be setup prior to election'
                )
        except Exception as message:
            print(
                r'Fatal error has occurred: {message}'.format(
                    message=message
                )
            )
            return False

        uri = r'{domain}/user/{candidate}.json'.format(
            domain=Election.DOMAIN,
            candidate=self.candidate
        )

        response = requests.get(uri)

        if (response.status_code != requests.codes.ok):
            raise Exception(
                'Unable to make successful request'
            )

        response = response.json()

        if 'error' in response:
            for error in response['errors']:
                raise Exception(
                    'Recieved an error: ' + error.pop(1).title()
                )

        first_id = None
        last_id = self.lastCommentId()

        for comment in response['data']['children']:
            if comment['data']['name'] == last_id:
                break

            if first_id is None:
                first_id = comment['data']['name']

            self.comments.append(comment)

        if first_id is not None:
            self.setLastCommentId(first_id)

        self._vote()

        return True

    """
    Begins election process
    """
    def _vote(self):
        for username, password in self.voters.items():
            if self._login(username, password) is True:
                for comment in self.comments:
                    print(
                        r'Voting on comment #{name} as {voter}.'.format(
                            name=comment['data']['name'],
                            voter=username
                        )
                    )

                    request = {
                        'id': comment['data']['name'],
                        'dir': 1,
                        'r': comment['data']['subreddit'],
                        'uh': self.client.modhash,
                        }

                    self.client.post(
                        Election.DOMAIN + '/api/vote',
                        data=request
                    )

                # Sleep
                print(
                    'Sleeping...'
                )
                time.sleep(10)

    """
    Starts a new user session using passed credentials

        Arguments:

            username
                Username of account that should will be casting his/her vote

            password
                Password for this account
    """
    def _login(self, username, password):
        # Construct request data
        request = {
            'user': username,
            'passwd': password,
            'api_type': 'json'
        }

        # Create new session
        self.client = requests.session()

        # We limit number of attempts in order to prevent API abuse
        attempts = int(0)

        while attempts < 3:
            try:
                print(
                    r'Attempting to login to voter account: {username}'.format(
                        username=username
                    )
                )

                response = self.client.post(
                    Election.DOMAIN + '/api/login',
                    data=request
                )

                if (response.status_code != requests.codes.ok):
                    raise Exception(
                        'Unable to make successful request'
                    )

                response = response.json()

                if 'errors' in response['json']:
                    for error in response['json']['errors']:
                        raise Exception(
                            'Recieved an API error: ' + error.pop(1).title()
                        )

                self.client.modhash = response['json']['data']['modhash']
                self.client.user = username

                return True
            except Exception as e:
                # Substract from attempts
                attempts += 1

                print(e)
                print(
                    'Sleeping for 30 seconds before trying again'
                )

                time.sleep(15)


def main():
    parser = argparse.ArgumentParser(description='Reddit election.')
    parser.add_argument(
        '--candidate',
        dest='candidate',
        action='store',
        help='--candidate username'
    )
    parser.add_argument(
        '--voters',
        dest='voters',
        action='store',
        help='--voters voter1:password,voter2:password}'
    )

    # Parse passed arguments for processing
    arguments = parser.parse_args()

    # Setup election
    election = Election()
    election.setCandidate(arguments.candidate)

    # Process voters
    voters = arguments.voters.split(',')

    for voter in voters:
        (username, password) = voter.split(':')
        election.addVoter(username, password)

    # Begin election
    election.begin()

if __name__ == '__main__':
    sys.exit(main())
