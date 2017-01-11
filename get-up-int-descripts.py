#!/usr/bin/python
 
import requests
import json
import getpass
 
"""
Modify these please
 
"""
### Get Input ###
prompt = '>'
print "Enter hostname or ip address of the Nexus switch:"
switchname = raw_input(prompt)
print "Enter the switch username:"
switchuser = raw_input(prompt)
switchpassword = getpass.getpass("Insert the switch password: ")
######
 
url="http://%s/ins" %(switchname)
 
myheaders={'content-type':'application/json-rpc'}
payload=[
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "show int",
      "version": 1
    },
    "id": 1
  }
]
response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
 
#print type(response)
 
listofints = response["result"]["body"]["TABLE_interface"]["ROW_interface"]
#print type(listofints)
 
for i in range(0,len(listofints)):
        if 'state' in listofints[i]:
                if listofints[i]['state'] == "up":
                        if 'desc' in listofints[i]:
                                print "%s, %s" %(listofints[i]["interface"], listofints[i]["desc"])
                        else:
                                print "%s" %(listofints[i]["interface"])