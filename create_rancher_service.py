#!/usr/bin/python2 -u
#-----------------------------------------------------------------------
# Author: Germain LEFEBVRE
#-----------------------------------------------------------------------
# Description: Create service
#-----------------------------------------------------------------------
# Parameters:
#  short  long                  default  Required  Description
#  -E     --env                 NULL     yes       Name of the Environment
#  -S     --stack-name          NULL     yes       Name of the Stack
#  -s     --service-name        NULL     yes       Name of the Service
#  -Sd    --service-description NULL     no        Description of the Stack
#-----------------------------------------------------------------------
# ChangeLog:
#    [2017-12-28] v0.1 : Create service with envName, stackName, serviceName
#                        and serviceDescription in LaunchConfig.
#-----------------------------------------------------------------------
# Todo:
#-----------------------------------------------------------------------
# Return Values :
#   0 : Succeded with no change
#   1 : Failed
#  50 : Succeded with changes
#-----------------------------------------------------------------------
# Example:
#   ./create_rancher_service.py -E Default -S Activities -s sports
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
                        help="Name of the Environment")
    parser.add_argument('-S', '--stack-name',
                        required=True,
                        help="Name of the Stack")
    parser.add_argument('-s', '--service-name',
                        required=True,
                        help="Name of the Service")
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


# Description: Get Rancher Stack ID
#   Inputs:
#     #1: (string) Rancher Env Name
#     #2: (sring) Rancher Stack Name
#   Outputs:
#     #1: (int) Rancher Stack ID
#     Quit if does not exist
def getStackId(envName,stackName):
  envId = getEnvId(envName)
  stackId = existStackId(envName, stackName)
  if stackId == False:
    print("Error: Stack '" + stackName + "' does not exist.")
    sys.exit(1)
  return stackId


# Description: Get Rancher Service ID.
#   Inputs:
#     #1: (string) Rancher Env Name
#     #2: (string) Rancher Stack Name
#     #3: (string) Rancher Service Name
#   Outputs:
#     #1: (int) Rancher Service ID
#         (boolean=False) Rancher Service does not exist
def existServiceId(envName,stackName,serviceName):
  envId = getEnvId(envName)
  stackId = getStackId(envName,stackName)
  r = requests.get(RANCHER_URL + 'v2-beta' +
                   '/services/?name=' + serviceName +
                   '&stackId=' + stackId +
                   '&accountId=' + envId,
                   auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY))
  if len(r.json()['data']) == 0:
    return False
  return r.json()['data'][0]['id']


# Description: Get Rancher Service ID
#   Inputs:
#     #1: (string) Rancher Env Name
#     #2: (string) Rancher Stack Name
#     #3: (string) Rancher Service Name
#   Outputs:
#     #1: (int) Rancher Service ID
#     Quit if does not exist
def getServiceId(envName,stackName,ServiceName):
  envId = getEnvId(envName)
  stackId = getStackId(stackName)
  serviceId = existServiceId(envName, stackName)
  if stackId == False:
    print("Error: Service '" + serviceName + "' does not exist.")
    sys.exit(1)
  return stackId


# Description: Get Rancher Stack LaunchConfig
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


# Description: Get Rancher Service LaunchConfig
#   Inputs:
#     #1: (int) Rancher Env ID
#     #2: (int) Rancher Stack ID
#     #2: (int) Rancher Service ID
#   Outputs:
#     #1: (list) Launchconfig retrieved from Service
def getServiceLaunchconfig(serviceId):
  result = {}
  r = requests.get(RANCHER_URL + 'v2-beta' +
                   '/services/' + serviceId,
                   auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY))
  return r.json()['launchConfig']


# Description: Compare values from 2 JSON objects (complexity nn)
#     Right object is permissive compared to left object. An attribute present
#     in right object but not in left wont block. But an attribute present in
#     left object but not right will break the actions.
#   Inputs:
#     #1: (json) JSON object
#     #2: (json) JSON object
#   Outputs:
#     #1: (boolean) True=Equal False=Different
def areLaunchconfigEqual(left,right):
  l_flag = True
  for keyLeft in left.keys():
    #for keyRight in right.keys():
    if keyLeft in right.keys():
    #if right[keyLeft] is not None:
      if left[keyLeft] != right[keyLeft]:
        print "Need update"
        l_flag = False
        break
    else:
      print "Need update"
      l_flag = False
      break
    if l_flag == False:
      break
  return l_flag


# Description: Set Rancher Service
#   Inputs:
#     #1: (string) Rancher Env Name
#     #2: (string) Rancher Stack Name
#     #3: (string) Rancher Service Name
#   Outputs:
#     #1:
def setService(envName,stackName,serviceName):
  global rc
  rc=0

  # Get Rancher Env
  envId = getEnvId(envName)
  # Get Rancher Stack
  stackId = getStackId(envName,stackName)
  # Get Rancher Service
  serviceId = existServiceId(envName,stackName,serviceName)

  # Set Service JSON Template
  payload = {
    "type":"service",
    "name": serviceName,
    "stackId": stackId,
    "startOnCreate": True,
    "scale": 1,
    "launchConfig":{
      "type":"launchConfig",
      "dataVolumes":[
      ],
      "environment":{
      },
      "imageUuid":"docker:library/alpine:latest",
      "instanceTriggeredStop":"stop",
      "kind":"container",
      "labels":{
        "io.rancher.container.pull_image": "always"
      },
      "logConfig":{
        "type":"logConfig"
      },
      "memoryReservation": 134217728,
      "networkMode":"managed",
      "privileged": "false",
      "publishAllPorts": False,
      "readOnly": False,
      "runInit": False,
      "startOnCreate": True,
      "stdinOpen": True,
      "system": False,
      "tty": True,
      "user":"root",
      "version":"0",
      "vcpu":1
    }
  }

  # If Service does not exist then create it
  if serviceId == False:
    r = requests.post(RANCHER_URL + 'v2-beta' +
                      '/projects/' + envId +
                      '/services' +
                      '?stackId=' + stackId,
                      headers=headers,
                      auth=(RANCHER_ACCESS_KEY, RANCHER_SECRET_KEY),
                      json=payload)
    # If error print stacktrace
    if r.json()['baseType'] in ['error']:
      print r.json()
      sys.exit(1)
    # Success
    print "Service created"
    rc=50
  else:
    print "Service already created"


# MAIN FUNCTION
def main():
  args = parseArguments()

  # Users Parameters
  p_envName = args.env
  p_stackName = args.stack_name
  p_serviceName = [args.service_name]

  # Show variables
  print "Environment: %s" % p_envName
  print "Stack: %s" % p_stackName
  print "Service(s): %s" % " ".join(str(x) for x in p_serviceName)

  # Create services
  for serviceName in p_serviceName:
    print("-------------------")
    print("Service: %s" % serviceName)
    setService(p_envName, p_stackName, serviceName)

  sys.exit(rc)

if __name__ == "__main__":
  main()
