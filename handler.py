import json
import msal
import requests
import boto3
import sys
#import re

secret_manager_arn = "arn:aws:secretsmanager:us-east-1:********" 
client = boto3.client("secretsmanager")
response = client.get_secret_value(SecretId = (secret_manager_arn))
secret_dict = json.loads(response["SecretString"])

""" jamf pro config """
jamf_hostname = secret_dict['jamfhostname']
jamfuser = secret_dict['jamfuser']
jamfpass = secret_dict['jamfpass']

""" msal config """
config = {
  'client_id': secret_dict['client_id'] ,
  'client_secret': secret_dict['client_secret'], 
  'authority': secret_dict['authority'],
  'scope': ['https://graph.microsoft.com/.default'] 
}

""" create an msal instance """
client = msal.ConfidentialClientApplication(config['client_id'], authority=config['authority'], client_credential=config['client_secret'])

""" optional parameter 'pagination' can be set to False to return only first page of graph results """
def make_graph_call(url, pagination=True):
  # Firstly, try to lookup an access token in cache
  token_result = client.acquire_token_silent(config['scope'], account=None)

  if token_result:
    print('Access token was loaded from cache.')

  if not token_result:
    token_result = client.acquire_token_for_client(scopes=config['scope'])
    print('New access token aquired from AAD')

  if 'access_token' in token_result:
    headers = {'Authorization': 'Bearer ' + token_result['access_token']}
    graph_results = []

    while url:
      try:
        graph_result = requests.get(url=url, headers=headers).json()
        graph_results.extend(graph_result['value'])
        if (pagination == True):
          url = graph_result['@odata.nextLink']
        else:
          url = None
      except:
         break
  else:
    print(token_result.get('error'))
    print(token_result.get('error_description'))
    print(token_result.get('correlation'))

  return graph_results


def validate(event, context):
    event_body = json.loads(event['body'])
    user = event_body['email']
    group = event_body['group']
    serialNumber = event_body['serialNumber']
    url = f'https://graph.microsoft.com/v1.0/users/{user}/memberOf'
    
    """ validate email syntax if required """
    #email_regex = re.compile('^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$')
    #matches = email_regex.match(event_body['email']) != None
    
    print(f'json payload received from endpoint: {serialNumber}')
    print(f'received upn: {user}')
    print(f'received group: {group}')
    
    """ lets check the received sn exists in jamf """
    api_token = get_token()
    headers = {'Accept': 'application/json', 'Authorization': 'Bearer ' + api_token}
    endpoint = f'{jamf_hostname}/JSSResource/computers/match/{serialNumber}'
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
      """ create dict from json response"""
      data = json.loads(response.content.decode('utf-8'))
      try :
        """ the supplied sn supplied exists in jamf """
        serialNumberFound = data['computers'][0]['serial_number']
      except IndexError:
        """ causes an index error if the sn is not found as jamf just returns an empty list """
        print(f'supplied serial number {serialNumber} was not found in jamf server {jamf_hostname}....exiting')
        sys.exit(1)
      
      print(f'supplied serial number {serialNumber} matches {serialNumberFound} in jamf server {jamf_hostname}.')
      
      """ query ms graph api for supplied user membership status """
      results = make_graph_call(url, pagination=False)
      found = 0
      for result in results:
        group_name=result['displayName']
        if group_name == group:
          """ user was found in group """
          print(f'user {user} is a member of {group}.')
          found = 1
          print(f'returnng result {found} to endpoint')
      
      response = {
        'statusCode': 200,
        'body': json.dumps({ 'result': found })
      }
  
      return response
                        
    else:
      print('...error:',response.content.decode('utf-8'))
  
""" request jamf api token """
def get_token():

    token_url = f'{jamf_hostname}/api/v1/auth/token'
    headers = {'Accept': 'application/json', }
    response = requests.post(url=token_url, headers=headers, auth=(jamfuser, jamfpass))
    response_json = response.json()
    print(f'...api token obtained from {jamf_hostname}')
    return response_json['token']

""" invalidate jamf api token """
def drop_token(api_token):

    token_drop_url = f'{jamf_hostname}/api/v1/auth/invalidate-token'
    headers = {'Accept': '*/*', 'Authorization': 'Bearer ' + api_token}
    response = requests.post(url=token_drop_url, headers=headers)

    if response.status_code == 204:
        print('...api token invalidated.')

    else:
        print('...error invalidating api token.')