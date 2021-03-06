#!/usr/bin/env python
"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
import time
import sys
from StringIO import StringIO as BytesIO
import json
from resource_management.core.logger import Logger
import urllib2, base64, httplib

class Rangeradmin:
  sInstance = None
  def __init__(self, url= 'http://localhost:6080'):
    
    self.baseUrl      =  url 
    self.urlLogin     = self.baseUrl + '/login.jsp'
    self.urlLoginPost = self.baseUrl + '/j_spring_security_check'
    self.urlRepos     = self.baseUrl + '/service/assets/assets'
    self.urlReposPub  = self.baseUrl + '/service/public/api/repository'
    self.urlPolicies  = self.baseUrl + '/service/public/api/policy'
    self.urlGroups    = self.baseUrl + '/service/xusers/groups'
    self.urlUsers     = self.baseUrl + '/service/xusers/users'   
    self.urlSecUsers  = self.baseUrl + '/service/xusers/secure/users'   

    self.session    = None
    self.isLoggedIn = False

  def get_repository_by_name_urllib2(self, name, component, status, usernamepassword):
    try:
      searchRepoURL = self.urlReposPub + "?name=" + name + "&type=" + component + "&status=" + status
      request = urllib2.Request(searchRepoURL)
      base64string = base64.encodestring(usernamepassword).replace('\n', '')
      request.add_header("Content-Type", "application/json")   
      request.add_header("Accept", "application/json")  
      request.add_header("Authorization", "Basic %s" % base64string)   
      result = urllib2.urlopen(request)
      response_code =  result.getcode()
      response = json.loads(result.read())

      if response_code == 200 and len(response['vXRepositories']) > 0:
        for repo in response['vXRepositories']:
          repoDump = json.loads(json.JSONEncoder().encode(repo))
          if repoDump['name'] == name:
            return repoDump
        return None
      else:
        return None
    except urllib2.URLError, e:
      if isinstance(e, urllib2.HTTPError):
          Logger.error("HTTP Code: %s" % e.code)
          Logger.error("HTTP Data: %s" % e.read())
      else:
          Logger.error("Error : %s" % (e.reason))
      return None
    except httplib.BadStatusLine:
      Logger.error("Ranger Admin service is not reachable, please restart the service and then try again")
      return None

  def create_repository_urllib2(self, data, usernamepassword):
    try:
      searchRepoURL = self.urlReposPub
      base64string = base64.encodestring('%s' % (usernamepassword)).replace('\n', '')
      headers = {
        'Accept': 'application/json',
        "Content-Type": "application/json"
      }
      request = urllib2.Request(searchRepoURL, data, headers)
      request.add_header("Authorization", "Basic %s" % base64string)   
      result = urllib2.urlopen(request)
      response_code =  result.getcode()
      response = json.loads(json.JSONEncoder().encode(result.read()))
      if response_code == 200 :
        Logger.info('Repository created Successfully')
        #Get Policies 
        repoData     = json.loads(data)
        repoName     = repoData['name']
        typeOfPolicy = repoData['repositoryType']
        ##Get Policies by repo name
        policyList = self.get_policy_by_repo_name(name=repoName, component=typeOfPolicy, status="true", usernamepassword=usernamepassword)
        if (len(policyList)) > 0 : 
          policiesUpdateCount = 0
          for policy in policyList:
            updatedPolicyObj = self.get_policy_params(typeOfPolicy,policy)
            policyResCode, policyResponse = self.update_ranger_policy(updatedPolicyObj['id'], json.dumps(updatedPolicyObj), usernamepassword)
            if policyResCode == 200:
              policiesUpdateCount = policiesUpdateCount+1
            else:
              Logger.info('Policy Update failed')  
          ##Check for count of updated policies
          if len(policyList) == policiesUpdateCount:
            Logger.info("Ranger Repository created successfully and policies updated successfully providing ambari-qa user all permissions")
            return response
          else:
            return None
        else:
          Logger.info("Policies not found for the newly created Repository")
        return  None
      else:
        Logger.info('Repository creation failed')
        return None  
    except urllib2.URLError, e:
      if isinstance(e, urllib2.HTTPError):
          Logger.error("HTTP Code: %s" % e.code)
          Logger.error("HTTP Data: %s" % e.read())
      else:
          Logger.error("Error: %s" % (e.reason))
      return None
    except httplib.BadStatusLine:
      Logger.error("Ranger Admin service is not reachable, please restart the service and then try again")
      return None

  def check_ranger_login_urllib2(self, url,usernamepassword ):
    try:
      request = urllib2.Request(url)
      base64string = base64.encodestring(usernamepassword).replace('\n', '')
      request.add_header("Content-Type", "application/json")   
      request.add_header("Accept", "application/json")  
      request.add_header("Authorization", "Basic %s" % base64string)   
      result = urllib2.urlopen(request)
      response = result.read()
      response_code =  result.getcode()
      return response_code, response
    except urllib2.URLError, e:
      if isinstance(e, urllib2.HTTPError):
          Logger.error("HTTP Code: %s" % e.code)
          Logger.error("HTTP Data: %s" % e.read())
      else:
          Logger.error("Error : %s" % (e.reason))
      return None, None
    except httplib.BadStatusLine, e:
      Logger.error("Ranger Admin service is not reachable, please restart the service and then try again")
      return None, None      

  def get_policy_by_repo_name(self, name, component, status, usernamepassword):
    try:
      searchPolicyURL = self.urlPolicies + "?repositoryName=" + name + "&repositoryType=" + component + "&isEnabled=" + status
      request = urllib2.Request(searchPolicyURL)
      base64string = base64.encodestring(usernamepassword).replace('\n', '')
      request.add_header("Content-Type", "application/json")   
      request.add_header("Accept", "application/json")  
      request.add_header("Authorization", "Basic %s" % base64string)   
      result = urllib2.urlopen(request)
      response_code =  result.getcode()
      response = json.loads(result.read())
      if response_code == 200 and len(response['vXPolicies']) > 0:
          return response['vXPolicies']
      else:
        return None
    except urllib2.URLError, e:
      if isinstance(e, urllib2.HTTPError):
          Logger.error("HTTP Code: %s" % e.code)
          Logger.error("HTTP Data: %s" % e.read())
      else:
          Logger.error("Error: %s" % (e.reason))
      return None
    except httplib.BadStatusLine:
      Logger.error("Ranger Admin service is not reachable, please restart the service and then try again")
      return None

  def update_ranger_policy(self, policyId, data, usernamepassword):
    try:
      searchRepoURL = self.urlPolicies +"/"+str(policyId)
      base64string = base64.encodestring('%s' % (usernamepassword)).replace('\n', '')
      headers = {
        'Accept': 'application/json',
        "Content-Type": "application/json"
      }
      request = urllib2.Request(searchRepoURL, data, headers)
      request.add_header("Authorization", "Basic %s" % base64string)   
      request.get_method = lambda: 'PUT'
      result = urllib2.urlopen(request)
      response_code =  result.getcode()
      response = json.loads(json.JSONEncoder().encode(result.read()))
      if response_code == 200 :
        Logger.info('Policy updated Successfully')
        return response_code, response
      else:
        Logger.error('Update Policy failed')
        return None, None
    except urllib2.URLError, e:
      if isinstance(e, urllib2.HTTPError):
          Logger.error("HTTP Code: %s" % e.code)
          Logger.error("HTTP Data: %s" % e.read())
      else:
          Logger.error("Error: %s" % (e.reason))
      return None, None
    except httplib.BadStatusLine:
      Logger.error("Ranger Admin service is not reachable, please restart the service and then try again")
      return None, None

  def get_policy_params(self, typeOfPolicy,policyObj): 
    
    typeOfPolicy = typeOfPolicy.lower()
    if typeOfPolicy == "hdfs":
      policyObj['permMapList'] = [{'userList':['ambari-qa'],'permList':  ['Read','Write', 'Execute', 'Admin']}]
    elif typeOfPolicy == "hive":
      policyObj['permMapList'] = [{'userList':['ambari-qa'], 'permList':[ 'Select','Update', 'Create', 'Drop', 'Alter', 'Index', 'Lock', 'All', 'Admin' ]}]
    elif typeOfPolicy == "hbase":
      policyObj['permMapList'] = [{'userList':['ambari-qa'],'permList':[ 'Read', 'Write', 'Create', 'Admin']}]
    elif typeOfPolicy == "knox":
      policyObj['permMapList'] = [{'userList':['ambari-qa'], 'permList': ['Allow','Admin']}]
    elif typeOfPolicy == "storm" : 
      policyObj['permMapList'] = [{'userList':['ambari-qa'], 'permList':[ 'Submit Topology', 'File Upload', 'Get Nimbus Conf', 'Get Cluster Info', 'File Download', 'Kill Topology', 'Rebalance', 'Activate','Deactivate', 'Get Topology Conf', 'Get Topology', 'Get User Topology', 'Get Topology Info', 'Upload New Credential', 'Admin']}]
    return policyObj

