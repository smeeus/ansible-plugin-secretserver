#!/usr/bin/python

# The MIT License (MIT)
#
# Copyright (c) 2018 Sven Meeus / Framed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import (absolute_import, division, print_function)

# from ansible import utils, errors
# from ansible.plugins.lookup import LookupBase

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.plugins.lookup import LookupBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

import os
import getpass

from urlparse import urlparse
from urlparse import urljoin

try:
    import json
except ImportError:
    import simplejson as json

requests_installed=True
try:
    import requests
except ImportError:
    requests_installed=False

__metaclass__ = type

# Reuse code from ARA project config.py
from ansible import __version__ as ansible_version
from ansible.constants import get_config
try:
    from ansible.constants import load_config_file
except ImportError:
    # Ansible 2.4 no longer provides load_config_file, this is handled further
    # down
    from ansible.config.manager import find_ini_config_file
    # Also, don't scream deprecated things at us
    import ansible.constants
    ansible.constants._deprecated = lambda *args: None
from distutils.version import LooseVersion
from six.moves import configparser

def _secretserver_config(config, key, env_var, default=None, section='secretserver', value_type=None):
    """
    Wrapper around Ansible's get_config backward/forward compatibility
    """
    if default is None:
        try:
            # We're using env_var as keys in the DEFAULTS dict
            default = DEFAULTS.get(env_var)
        except KeyError as e:
            msg = 'There is no default value for {0}: {1}'.format(key, str(e))
            raise KeyError(msg)

    # >= 2.3.0.0 (NOTE: Ansible trunk versioning scheme has 3 digits, not 4)
    if LooseVersion(ansible_version) >= LooseVersion('2.3.0'):
        return get_config(config, section, key, env_var, default,
                          value_type=value_type)

    # < 2.3.0.0 compatibility
    if value_type is None:
        return get_config(config, section, key, env_var, default)

    args = {
        'boolean': dict(boolean=True),
        'integer': dict(integer=True),
        'list': dict(islist=True),
        'tmppath': dict(istmppath=True)
    }
    return get_config(config, section, key, env_var, default,
                      **args[value_type])

DEFAULTS = {
    'SECRETSERVER_HOST': os.environ["SECRETSERVER_HOST"],
    'SECRETSERVER_USERNAME': os.environ["SECRETSERVER_USERNAME"],
    'SECRETSERVER_PASSWORD': os.environ["SECRETSERVER_PASSWORD"]
}

# Bootstrap Ansible configuration
# Ansible >=2.4 takes care of loading the configuration file itself
if LooseVersion(ansible_version) < LooseVersion('2.4.0'):
    config, path = load_config_file()
else:
    path = find_ini_config_file()
    config = configparser.ConfigParser()
    if path is not None:
        config.read(path)

SECRETSERVER_HOST = _secretserver_config(config, 'host', 'SECRETSERVER_HOST', default=DEFAULTS['SECRETSERVER_HOST'])
SECRETSERVER_USERNAME = _secretserver_config(config, 'username', 'SECRETSERVER_USERNAME', default=DEFAULTS['SECRETSERVER_USERNAME'])
SECRETSERVER_PASSWORD = _secretserver_config(config, 'password', 'SECRETSERVER_PASSWORD', default=DEFAULTS['SECRETSERVER_PASSWORD'])


def _rest_url(baseurl, path, usebase=True):
    # print urljoin(_ssbaseurl, ("/api/v1" if usebase == True else "") + path)
    return urljoin(baseurl, ("/api/v1" if usebase == True else "") + path)

def rest_get_token(baseurl, username, password):
    return requests.post(_rest_url(baseurl, "/oauth2/token", False), data = {
        "username": username,
        "password": password,
        "grant_type": "password",
        })

def rest_search_secrets(baseurl, searchtext="", headers={}):
    return requests.get(_rest_url(baseurl, "/secrets"), params = {
        "filter.searchText": searchtext,
    }, headers = headers)

def rest_get_secret(baseurl, secretid=0, headers={}):
    return requests.get(_rest_url(baseurl, "/secrets/%s" % secretid), headers = headers)

def get_token(baseurl, user, pwd):
    resp = rest_get_token(baseurl, user, pwd)
    if resp.status_code != 200:
        raise AnsibleError("Cannot get token: %s - %s" % (resp.status_code, resp.text))
    display.debug("Get token success: %s - %s" % (resp.status_code, resp.text))
    display.debug("Response JSON: {}" % resp.json())
    token = resp.json()["access_token"]
    display.debug("token: %s" % token)
    return token

def search_secrets(baseurl, searchtext="", headers={}):
    resp = rest_search_secrets(baseurl, searchtext, headers)
    if resp.status_code != 200:
        raise AnsibleError("Cannot search secret: %s - %s" % (resp.status_code, resp.text))
    display.debug("Search secrets success: %s - %s" % (resp.status_code, resp.text))
    display.debug("Response JSON: {}" % resp.json())
    records = resp.json()["records"]
    display.debug("records: {}" % records)
    return records

def get_secret_ids(searchtext="", records=[]):
    searchids = []
    for record in records:
        display.debug(record)
        searchid = 0
        recordname = record["name"]
        if recordname == searchtext:
            searchids.append(record["id"])
    display.debug("searchids: {}" % searchids)
    return searchids

def get_secret(baseurl, secretid=0, headers={}):
    resp = rest_get_secret(baseurl, secretid, headers)
    if resp.status_code != 200:
        raise AnsibleError("Cannot get secret: %s - %s" % (resp.status_code, resp.text))
    display.debug("Get secret success: %s - %s" % (resp.status_code, resp.text))
    display.debug("Response JSON: {}" % resp.json())
    secretitems = resp.json()["items"]
    display.debug("secretitems: {}" % secretitems)
    return secretitems


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        # Get credentials from environment variables
        sshost=SECRETSERVER_HOST
        ssuser=SECRETSERVER_USERNAME
        sspass=SECRETSERVER_PASSWORD

        # Define base url
        ssbaseurl = "https://%s" % sshost

        # Initialize the final return data array
        ret = []

        # the item to search for
        searchtext = ""
        # the field type to get
        searchtype = ""

        # Python requests module validation
        if not requests_installed:
            raise AnsibleError("Python requests module is not installed")

        # Get authentication token
        token = get_token(ssbaseurl, ssuser, sspass)

        # Set authentication header
        token_header = "Bearer " + token
        headers = {"Authorization": token_header}

        # Get item and type from passed terms
        for term in terms:
            display.debug("File lookup term: %s" % term)

            searchtext = term.split(".")[0]
            searchtype = term.split(".")[1]
            display.debug("searchtext: %s" % searchtext)
            display.debug("searchtype: %s" % searchtype)

            ### Search for secrets
            records = search_secrets(ssbaseurl, searchtext, headers)

            ### Get secret ids
            searchids = get_secret_ids(searchtext, records)

            for searchid in searchids:

                ### Get secret data
                secretitems = get_secret(ssbaseurl, searchid, headers)

                ### Check search type
                if searchtype == "id":
                    ret.append(searchid)
                else:
                    for item in secretitems:
                        display.debug(item)
                        if searchtype == "password":
                            if item["fieldName"] == "Password":
                                ret.append(item["itemValue"])
                        elif searchtype == "username":
                            if item["fieldName"] == "Username":
                                ret.append(item["itemValue"])
                        elif searchtype == "notes":
                            if item["fieldName"] == "Notes":
                                ret.append(item["itemValue"])
                        else:
                            raise AnsibleError("Unknow request type '%s'. Use 'password', 'username', 'id' or 'notes'" % searchtype)

                # Uncomment if you always want to get a single item
                # break

        # Return final data array
        return ret
