#!/usr/bin/env python
import json
import requests
import sys
import time
import json
from datetime import datetime, timedelta
from urllib import quote


# Authentication for user filing issue (must have read/write access to
# repository to add issue to)
USERNAME = 'REPLACE_ME'
PASSWORD = 'REPLACE_ME'

# The repository to add this issue to
REPO_OWNER = 'REPLACE_ME'
REPO_NAME = 'REPLACE_ME'
POCKET_CONSUMER_KEY = "REPLACE_ME"
POCKET_ACCESS_TOKEN = "REPLACE_ME"

since = '2018-03-10T20:09:31Z' #TODO


def get_pocket_since(day):
    yesterday = datetime.today() - timedelta(day)
    timestamp = time.mktime(yesterday.timetuple())
    return timestamp


def get_pocket_items():
    pocket_items = []
    pocket_since = get_pocket_since(3)
    url = "https://getpocket.com/v3/get?consumer_key=%s&access_token=%s&since=%d" %(POCKET_CONSUMER_KEY, POCKET_ACCESS_TOKEN, pocket_since)

    resp = requests.get(url)

    items = resp.json()

    for detail in items['list'].itervalues():
        pocket_items.append(detail)

    return pocket_items


def search_github_issue(title):
    # wired,use since=2018-03-02T12:11:22ZZ with addtional Z,will stop on last issues,or will always get last one.
    url = "https://api.github.com/search/issues?sort=created&order=asc&q="
    q = "%s+repo:%s/%s" % (quote(title.encode('utf-8')), REPO_OWNER, REPO_NAME, )
    url = url + q
    print(url)
    headers = {
        'Accept': 'application/vnd.github.symmetra-preview+json',
    }
    resp = requests.get(url, auth=(USERNAME, PASSWORD))
    if resp.status_code > 400:
        print resp.status_code
        return None
    issues = resp.json()
    # print issues
    return issues['items']


def make_github_issue(title, body=None, assignee=None, milestone=None, labels=None):
    '''Create an issue on github.com using the given parameters.'''
    # Our url to create issues via POST
    url = 'https://api.github.com/repos/%s/%s/issues' % (REPO_OWNER, REPO_NAME)
    # Create an authenticated session to create the issue
    # Create our issue
    # TODO format this payload by paramters
    issue = {'title': title,
             'body': body,
             'assignee': assignee,
             # 'milestone': milestone,
             # 'labels': labels
             }

    headers = {
        'Accept': 'application/vnd.github.symmetra-preview+json',
    }

    # Add the issue to our repository
    r = requests.post(url, data=json.dumps(issue), auth=(USERNAME, PASSWORD))

    if r.status_code == 201:
        print('Successfully created Issue "%s"' % title)
    else:
        print('Could not create Issue "%s"' % title)
        print('Response:', r.content)


def main():
    # TODO get pocket items since
    pocket_items = get_pocket_items()
    for item in pocket_items:
        # print '-' * 80
        pocket_title = None

        # status == 1 : archived
        # status == 2 : deleted
        if item['status'] != "0":
            print item['status']
            continue

        try:
            pocket_title = item['resolved_title'] if 'resolved_title' in item else item['given_title']
        except Exception as e:
            print item
            print e

        if pocket_title is None or pocket_title == "":
            continue

        search_result = search_github_issue(pocket_title)
        time.sleep(1)
        # trigger rate limit of github,will try it later
        if search_result is None:
            continue

        pocket_imported = False
        for issue in search_result:
            if pocket_title == issue['title']:
                pocket_imported = True
                print "found issue: ", issue['title']
                break

        if pocket_imported:
            continue

        # print '0' * 80
        print 'making github issues.....: ', pocket_title
        resolved_url = item['resolved_url']
        excerpt = item['excerpt']
        added_at = item['time_added']
        added_at = datetime.fromtimestamp(int(added_at)).strftime('%Y-%m-%d %H:%M:%S')
        words = item['word_count']
        issue_body = "<a href='%s'>%s</a><br><br>%s<br>%s<br>%s" % (resolved_url, pocket_title, excerpt, added_at, words)

        make_github_issue(pocket_title, issue_body, assignee=REPO_OWNER, milestone=None, labels=None)

    pass


if __name__ == '__main__':
    main()
