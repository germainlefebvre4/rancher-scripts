#!/usr/bin/python2 -u
#-----------------------------------------------------------------------
# Author: Germain LEFEBVRE
#-----------------------------------------------------------------------
# Description: Create stack
#-----------------------------------------------------------------------
# Context:
#  - Docker version: 1.12.6
#  - Rancher version: 1.6.10
#-----------------------------------------------------------------------
# Parameters:
#  short  long                default  Required  Description
#  -E     --env               NULL     yes       Name of the Environment
#  -S     --stack-name        NULL     yes       Name of the Stack
#  -Sd    --stack-description NULL     yes       Description of the Stack
#-----------------------------------------------------------------------
# ChangeLog:
#    [2017-12-28] v0.2 : Compare Launchconfig. Add comments.
#    [2017-12-27] v0.1 : Create stack with envName, stackName and stackDescription.
#-----------------------------------------------------------------------
# Todo:
#  - Colorize status on upgrading
#  - Handle status upgraded when upgrading
#-----------------------------------------------------------------------
# Return Values :
#   0 : Succeded with no change
#   1 : Failed
#  50 : Succeded with changes
#-----------------------------------------------------------------------
# Example:
#   ./create_rancher_stack.py -S Activities
#-----------------------------------------------------------------------


# LIBRAIRIES
import argparse
import json
import time
import sys
import requests


# VARIABLES
# Global variables
global rc
global RANCHER_URL, RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY
global BINARIES_URL
global headers

headers = {'content-type': 'application/json'}

# Rancher parameters
RANCHER_URL = 'http://{{ rancher_master }}:8080/'
RANCHER_ACCESS_KEY = '{{ rancher_admin_user }}'
RANCHER_SECRET_KEY = '{{ rancher_admin_pass }}'
BINARIES_URL = '{{ binaries_url }}'


# FUNCTIONS
# Description: Parse arguments function
#   Inputs:
#     Nothing. Parse script parameters.
#   Outputs:
#     #1: (list) List of script parameters
def parseArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-E', '--env',
                        required=True,
                        help="Name of the environment")
    parser.add_argument('-S', '--stack-name',
                        required=True,
                        help="Name of the stack")
    parser.add_argument('-Sd', '--stack-description',
                        required=False,
                        help="Description of the stack")
    return parser.parse_args()


# Description: Get Rancher Env ID.
#   Inputs:
#     #1: (string) Rancher Env Name
#   Outputs:
#     #1: (int) Rancher Env ID
#         (boolean=False) Rancher Stack does not exist
def existEnvId(envName):
  r = requests.get(RANCHER_URL + 'v2-beta' +
                   '/projects?name=' + envName,
                   auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY))
  if len(r.json()['data']) == 0:
    return False
  return r.json()['data'][0]['id']


# Description: Get Rancher Env ID.
#   Inputs:
#     #1: (string) Rancher Env Name
#   Outputs:
#     #1: (int) Rancher Env ID
#     Quit if does not exist.
def getEnvId(envName):
  envId = existEnvId(envName)
  if envId == False:
    print("Error: Environment '" + envName + "' does not exist.")
    sys.exit(1)
  return envId


# Description: Get Rancher Stack ID.
#   Inputs:
#     #1: (string) Rancher Env Name
#     #2: (string) Rancher Stack Name
#   Outputs:
#     #1: (int) Rancher Stack ID
#         (boolean=False) Rancher Stack does not exist
def existStackId(envName,stackName):
  envId = getEnvId(envName)
  r = requests.get(RANCHER_URL + 'v2-beta' +
                   '/stacks/?name=' + stackName +
                   '&accountId=' + envId,
                   auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY))
  if len(r.json()['data']) == 0:
    return False
  return r.json()['data'][0]['id']


# Description: Get Rancher Env ID
#   Inputs:
#     #1: (string) Rancher Env Name
#     #2: (sring) Rancher Stack Name
#   Outputs:
#     #1: (int) Rancher Stack ID
#     Quit if does not exist
def getStackId(envName,stackName):
  envId = getEnvId(envName)
  stackId = existStackId(envName, stackname)
  if stackId == False:
    print("Error: Stack '" + stackName + "' does not exist.")
    sys.exit(1)
  return stackId


# Description
#   Inputs:
#     #1: (int) Rancher Env ID
#     #2: (int) Rancher Stack ID
#   Outputs:
#     #1: (list) Launchconfig retrieved from Stack
def getStackLaunchconfig(envId, stackId):
  result = {}
  r = requests.get(RANCHER_URL + 'v2-beta' +
                   '/stacks/' + stackId +
                   '?accountId=' + envId,
                   auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY))
  result['name'] = r.json()['name']
  result['description'] = r.json()['description']
  result['system'] = r.json()['system']
  result['dockerCompose'] = r.json()['dockerCompose']
  result['rancherCompose'] = r.json()['rancherCompose']
  return result


# Description: Compare values from 2 JSON objects (complexity n2)
#   Inputs:
#     #1: (json) JSON object
#     #2: (json) JSON object
#   Outputs:
#     #1: (boolean) True=Equal False=Different
def areLaunchconfigEqual(left,right):
  l_flag = True
  for keyLeft in left.keys():
    for keyRight in right.keys():
      if left[keyRight] is None or right[keyLeft] is None:
        print "Need update"
        l_flag = False
        break
      if left[keyLeft] != right[keyLeft] or left[keyRight] != right[keyRight]:
        print "Need update"
        l_flag = False
        break
    if l_flag == False:
      break
  return l_flag

# Description: Set Rancher Stack
#   Inputs:
#     #1: (string) Rancher Env Name
#     #2: (string) Rancher Stack Name
#     #3: (string) Rancher Stack Description
#   Outputs:
#     #1: (boolean) True=Equal False=Different
def setStack(envName, stackName, stackDescription):
  global rc
  rc=0
  # Set Stack JSON Template
  payload = {
    "name": stackName,
    "description": stackDescription,
    "system": False,
    "dockerCompose": "",
    "rancherCompose": ""
  }
  # Get Rancher Env
  envId = getEnvId(envName)
  # Get Rancher Stack
  stackId = existStackId(envName, stackName)
  # If Stack does not exist then create it
  if stackId == False:
    r = requests.post(RANCHER_URL + 'v2-beta' +
                      '/projects/' + envId +
                      '/stacks',
                      headers=headers,
                      auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY),
                      json=payload)
    print "Stack created"
    rc=50
    # If error print stacktrace
    if r.json()['baseType'] in ['error']:
      print r.json()
      sys.exit(1)
  else:
    # Get Stack Launchconfig
    launchconfig = getStackLaunchconfig(envId, stackId)
    # Compare current and desired Launchconfig
    isLcEqual = areLaunchconfigEqual(launchconfig, payload)
    # If comparison different then update Stack else do nothing
    if isLcEqual == False:
      r = requests.put(RANCHER_URL + 'v2-beta' +
                       '/projects/' + envId +
                       '/stacks/' + stackId,
                       headers=headers,
                       auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY),
                       json=payload)
      print "Stack updated"
      rc=50
      # If error print stacktrace
      if r.json()['baseType'] in ['error']:
        print r.json()
        sys.exit(1)

# MAIN FUNCTION
def main():
  args = parseArguments()

  # Users Parameters
  p_envName = args.env
  p_stackName = args.stack_name
  if args.stack_description is not None:
    p_stackDescription = args.stack_description
  else:
    p_stackDescription = p_stackName

  # Show variables
  print "Environment: %s" % p_envName
  print "Stack: %s" % p_stackName

  # Actions
  setStack(p_envName, p_stackName, p_stackDescription)

  sys.exit(rc)

if __name__ == "__main__":
  main()
