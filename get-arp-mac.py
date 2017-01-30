#!/usr/bin/python

import requests
import json
import getpass
import socket
import time
import datetime
import sys


listofswitches = ["sw1", "sw2"]


"""
Modify these please

"""
### Get Input ###
prompt = '>'
#print "Enter hostname or ip address of the Nexus switch:"
#switchname = raw_input(prompt)
print "Enter the switch username:"
switchuser = raw_input(prompt)
switchpassword = getpass.getpass("Insert the switch password: ")
######

#url="http://%s/ins" %(switchname)

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

payload2=[
  {
    "jsonrpc": "2.0",
    "method": "cli",
    "params": {
      "cmd": "show ip arp detail vrf all",
      "version": 1
    },
    "id": 1
  }
]
####
nameofoutput=sys.argv[0]
print "name of script: %s" %(nameofoutput)
starttime = datetime.datetime.now()
yr = getattr(starttime, 'year')
month = getattr(starttime, 'month')
day = getattr(starttime, 'day')
hour = getattr(starttime, 'hour')
minute =  getattr(starttime, 'minute')
sec =  getattr(starttime, 'second')
testoutput = "%s-%s-%s-%s-%s-%s" % (yr, month, day, hour, minute, sec)
#print testoutput
newoutfile = "%s.%s" % (nameofoutput, testoutput)
print "Output will be written to ./%s" % newoutfile
####

foutfile = open(newoutfile, 'w')

for sw in listofswitches:
	interfaceinfo = {}
	#interfaceinfo["interface"] = {}
	#interfaceinfo["interface"]["desc"] = {}
	#print type(interfaceinfo["interface"]["desc"])
	print "Processing switch %s..." %(sw)
	url="http://%s/ins" %(sw)
	response = requests.post(url,data=json.dumps(payload), headers=myheaders,auth=(switchuser,switchpassword)).json()
	response2 = requests.post(url,data=json.dumps(payload2), headers=myheaders,auth=(switchuser,switchpassword)).json()

	#print type(response)

	listofints = response["result"]["body"]["TABLE_interface"]["ROW_interface"]
	#print type(listofints)

	arpmaclist = response2["result"]["body"]["TABLE_vrf"]["ROW_vrf"]["TABLE_adj"]["ROW_adj"]
	#print type(arpmaclist)

	## GET THE INTERFACE DESCRIPTION ##
	print "SWITCH: %s" %(sw)
	for i in range(0,len(listofints)):
		if 'state' in listofints[i]:
			if listofints[i]['state'] == "up":
				intface=str(listofints[i]["interface"])
				# Create a new dictionary
				#interfaceinfo["interface"]=intface
			
				if 'desc' in listofints[i]:
					descript=str(listofints[i]["desc"])
					interfaceinfo[intface] = descript
					#print type(descript)
					#print "\t%s, %s" %(listofints[i]["interface"], descript) 
					print "\t%s, %s" %(intface, descript) 
				else:
					#print "\t%s" %(listofints[i]["interface"])
					#print "\t%s" %(intface)
					interfaceinfo[intface] = "No Descript"

## Let's get a look at the dictionary.
#	for k, v in interfaceinfo.iteritems():
#		print "key is %s, v is %s" %(k, v)

	print "SWITCH: %s" %(sw)	
	print >> foutfile, "SWITCH: %s" %(sw)	
	print >> foutfile, "\tSWITCH,IP ADDR,REVERSE DNS RESULTS,MAC ADDRESS,PHYSICAL INT,INTERFACE DESCRIPT,LOGICAL INTF"
	for j in range(0,len(arpmaclist)):
		
		#print arpmaclist[j]
		ip = arpmaclist[j]["ip-addr-out"]
		try:
			dnsrevlookup = socket.gethostbyaddr(ip)[0]
		except:
			dnsrevlookup = "no-rev-dns"

		#print "%s, %s, %s" %(arpmaclist[j]["mac"], arpmaclist[j]["ip-addr-out"], dnsrevlookup)
		try: 
			ipaddrout = arpmaclist[j]["ip-addr-out"] 	
		except:
			ipaddrout = "undefined"

		try:
                        mac = arpmaclist[j]["mac"]
                except:
                        mac = "undefined"


		try:
			phyintf = arpmaclist[j]["phy-intf"]
		except:
			phyintf = "undefined"

		try:
			intfout = arpmaclist[j]["intf-out"]
		except:
			intfout = "undefined"

		if phyintf in interfaceinfo:
			descriptforoutput = interfaceinfo[phyintf]
			#print descriptforoutput
		
		if "mgmt" not in phyintf: 
			print "\t%s, %s, %s, %s, %s, %s, %s" %(sw,ipaddrout,dnsrevlookup,mac,phyintf,descriptforoutput,intfout)
			print >> foutfile, "\t%s, %s, %s, %s, %s, %s, %s" %(sw,ipaddrout,dnsrevlookup,mac,phyintf,descriptforoutput,intfout)
	
