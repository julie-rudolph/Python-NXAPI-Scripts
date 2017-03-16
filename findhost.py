#!/usr/bin/python

import requests
import json
import getpass
import socket
import time
import datetime
import sys
import os
import pprint

### Suppress TLS and Certificate warnings from NXAPI HTTPS calls
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from requests.packages.urllib3.exceptions import InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
from requests.packages.urllib3.exceptions import SNIMissingWarning
requests.packages.urllib3.disable_warnings(SNIMissingWarning)

### Specify list of switches from which you would to retrieve data from.
# The default for now is the Sun Prairie Leaf Switches. The location will become an input from the user.
# The variable 'listofswitches' is what gets used by the script.
DataCenter1switches = ["proddc1switch1","proddc1switch2","proddc1switch3","etc"]
DataCenter2switches = ["proddc2switch1","proddc2switch2","proddc2switch3","etc"]
TESTSwitches = ["172.16.1.188"]
#######
listofswitches=TESTSwitches

### Are you using NXAPI over HTTP or HTTPS?
global apisecurity
apisecurity = "http"

## Specify and Initialize Global Variables
global arpresults
global macresults
global inputsdict
arpresults = {}
macresults = {}
inputsdict = {}


### Get Input From User ###
def GetInput():
        ipaddr = None
        macaddr = None
        inputs = {}
        prompt = '>'
        #print "Do you want to search Qts, SP or Both? (Q, S, B)."
        #location = raw_input(prompt)
        location = "S"
        print "################################################################################################"
        print "### Version 1.0 ####"
        print "### This script searches the Sun Prairie Data Center leaf switches for an ip address"
        print "### and returns arp entry/entries for that ip address.  It then uses those results to find"
        print "### the physical interface on which the host is currently active."
        print "### Finally, the current running configuration of the physical interface is printed to the screen."
        print "################################################################################################"
        #print "Do you want to search for IP Address or Mac Address? (I or M)."
        #searchtype = raw_input(prompt)
        searchtype = "I"

        if searchtype == "I":
                while ipaddr is None:
                        print "Enter IP Address of Host You are Looking For"
                        ipaddr = raw_input(prompt)
        elif searchtype == "M":
                while macaddr is None:
                        print "Enter MAC Address of Host You are Looking For"
                        macaddr = raw_input(prompt)
        print "Enter your network username."
        username = raw_input(prompt)
        switchpassword = getpass.getpass("Enter your network password: ")
        inputs["location"] = location
        inputs["searchtype"] = searchtype
        inputs["username"] = username
        inputs["switchpassword"] = switchpassword
        if ipaddr != None: 
                inputs["ipaddr"] = ipaddr
        if macaddr != None:
                inputs["macaddr"] = macaddr
        return inputs 


### Build the headers and payload that will be used in the NXAPI call.
def bldpayload(method,cmd):
        myheaders={'content-type':'application/json-rpc'}
        rpcmethod = method

        if rpcmethod == "cli_ascii":
                payload=[
                {
                "jsonrpc": "2.0",
                        "method": "cli_ascii",
                        "params": {
                          "cmd": cmd,
                           "version": 1
                        },
                        "id": 1
                 }
                ]
        else:
                payload=[
                {
                "jsonrpc": "2.0",
                        "method": "cli",
                        "params": {
                          "cmd": cmd,
                           "version": 1
                        },
                        "id": 1
                 }
                ]
        return myheaders,payload

### Process the results of 'show arp' and print them.
def procshowarp(showarpresponse,inputsdict):
        for switch,data in showarpresponse.iteritems():
                if int(data["result"]["body"]["TABLE_vrf"]["ROW_vrf"]["cnt-total"]) > 0:
                        arpresults[switch] = data["result"]["body"]["TABLE_vrf"]["ROW_vrf"]["TABLE_adj"]["ROW_adj"]
                        #print type(arpresults)
                elif int(data["result"]["body"]["TABLE_vrf"]["ROW_vrf"]["cnt-total"]) == 0:
                        print "\t%s not found." %(inputsdict["ipaddr"])
                else:
                        print "Something went wrong...."
                        exit()

        if bool(arpresults):
                print "\n### ARP RESULTS FOUND ###"
                print "\nSWITCHNAME\tIP ADDRESS\tMAC ADDRESS\tL3 INTERFACE"
                for sw,data in arpresults.iteritems():
                        ip=data["ip-addr-out"]
                        mac=data["mac"]
                        l3int=data["intf-out"]
                        print "%s\t%s\t%s\t%s" %(sw,ip,mac,l3int)
        else:
                print "No arp entries for %s found." %(inputsdict["ipaddr"])

        return arpresults

### This is where we actually make the NXAPI call and collect the response.
def runcmds(listofswitches,myheaders,cmdpayload,inputsdict):
        cmdonly = cmdpayload[0]["params"]["cmd"]
        cmdresponses = {}
        for sw in listofswitches:
                #print "\tChecking switch %s for '%s'..." %(sw,cmdonly)
                #url="https://%s/ins" %(sw)
		url = "%s://%s/ins" %(apisecurity,sw)
		#print "url2 is %s" %(url2)
                #url="http://%s/ins" %(sw)
                try:
                        cmdresponse = requests.post(url,data=json.dumps(cmdpayload), verify=False, headers=myheaders,auth=(inputsdict["username"],inputsdict["switchpassword"])).json()
                except:
                        print "\nProbably incorrect username or password.  Exiting the program." 
                        exit()
                cmdresponses[sw] = cmdresponse
        return cmdresponses 

### Not used in Version 1.0 but this generates the name of the output file to which 
### results of the script will be written.
def buildoutfile():
        nameofoutput=os.path.basename(sys.argv[0])
        starttime = datetime.datetime.now()
        yr = getattr(starttime, 'year')
        month = getattr(starttime, 'month')
        day = getattr(starttime, 'day')
        hour = getattr(starttime, 'hour')
        minute =  getattr(starttime, 'minute')
        sec =  getattr(starttime, 'second')
        timestamp = "%s-%s-%s-%s-%s-%s" % (yr, month, day, hour, minute, sec)
        #print testoutput
        newoutfile = "/tmp/%s.%s" % (nameofoutput, timestamp)
        #print "\n\nOutput will be written to %s\n" % newoutfile
        return newoutfile

### Defines the show arp command, calls the 'runcmds' function to run the command, and then removes empty results.
def runshowarp(listofswitches,inputsdict):
        showarprespclean = {}
        ip = inputsdict["ipaddr"]
        arpcmd = "show ip arp %s vrf all" %(ip)
        myheaders,showarppay = bldpayload("cli",arpcmd)
        print "\nSearching the switches for arp entries..."
        showarpresponses = runcmds(listofswitches,myheaders,showarppay,inputsdict)
        for k,v in showarpresponses.iteritems():
                if int(v["result"]["body"]["TABLE_vrf"]["ROW_vrf"]["cnt-total"]) > 0:
                        showarprespclean[k]=v
                else:
                        print "\t%s: %s Not found" %(k,ip) 

        return showarprespclean

### Defines the show mac command, calls the 'runcmds' function to ru the commmand, then removes empty responses
def runshowmac(listofswitches,arpresponses,inputsdict):
        showmacrespclean = {}
        listofmacs = []
        switchlist = arpresponses.keys()
        for switch,data in arpresponses.iteritems():
                macaddr = data["mac"]
                listofmacs.append(macaddr)

        if all(v == listofmacs[0] for v in listofmacs):
                #print "all macs equal"
                maccmd = "show mac address-table address %s" %(listofmacs[0])
                myheaders,showmacpay = bldpayload("cli",maccmd)
                print "\nFinding physical interface(s)...."
                showmacresponses = runcmds(switchlist,myheaders,showmacpay,inputsdict)

        for k,v in showmacresponses.iteritems():
                try:
                        v["result"]["body"]["TABLE_mac_address"]
                except KeyError:
                        ## This isn't actually used, i just needed an action here for syntactical purposes.
                        nomacs = k
                        #print "\tNo mac entries on %s" %(k)
                else:
                        #print "we have data"
                        showmacrespclean[k]=v

        return showmacrespclean

### Processes the reslts from show mac commmand and prints them.
def procshowmac(showmacresponses,inputsdict):
        print "\n### PHYSICAL INTERFACE(S) FOUND ###"
        for switch,data in showmacresponses.iteritems():
                #print "in proshowmac"
                #print switch
                #print json.dumps(data, indent=2)
                vlan = data["result"]["body"]["TABLE_mac_address"]["ROW_mac_address"]["disp_vlan"]
                phyint = data["result"]["body"]["TABLE_mac_address"]["ROW_mac_address"]["disp_port"]
                print "### Host is on switch %s, vlan %s, interface %s" %(switch,vlan,phyint)
                swlist = [switch]
                #print swlist
                showrunint = getshowrunint(swlist,phyint,inputsdict)

                for sw,value in showrunint.iteritems():
                        print "\n### CURRENT CONFIGURATION ON THE PHYSICAL INTERFACE: ###"
                        output=value["result"]["msg"]
                        print "%s" %(output)

### Use the NXAPI to get the output of "show run interface <int name>
### In Version 1.0 "switchlist" is actually a list of 1 switch.
def getshowrunint(switchlist,interface,inputsdict):
        showrunintcmd = "show run interface %s" %(interface)
        myheaders,showrunintpay = bldpayload("cli_ascii",showrunintcmd)
        #print "payload for ascii: "
        #print showrunintpay
        showrunintresponse = runcmds(switchlist,myheaders,showrunintpay,inputsdict)
        return showrunintresponse


### Version 1.0:
### - Get input from user.
### - Look for ip address in leaf switches on the fabric and report which switches have an arp entry.
### - Search for the mac address associated with that ip on switches that have arp entries for the host. Print that info.
### - Print out current interface configuration of interfaces on which that mac is located. 
def main():
        switcheswitharp =[]
        inputsdict = GetInput()
        #print inputsdict
        outfile = buildoutfile()
        #print outfile
        if inputsdict["searchtype"] == "I":
                showarpresponses=runshowarp(listofswitches,inputsdict)
                arpresults=procshowarp(showarpresponses,inputsdict)
                if bool(arpresults):
                        #print arpresults
                        arpvals = arpresults.values()
                        showmacresponses=runshowmac(listofswitches,arpresults,inputsdict)
                        procshowmac(showmacresponses,inputsdict)

if __name__ == '__main__':
        main()

