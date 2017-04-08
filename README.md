# Python-NXAPI-Scripts

# get-arp-mac.py
1. use nxapi to retrieve the following information from a list of switches and output to screen and file.  The information presented is:

SWITCH,IP ADDR,REVERSE DNS RESULTS,MAC ADDRESS,PHYSICAL INT,INTERFACE DESCRIPT,LOGICAL INTF

# findhost.py
1. Ask user for an ip address to search for.
2. Search the provided list of switches to find the arp entry for the host.  The list of switches is hardcoded into the script. 
3. Find the mac address entry.
4. Find the interface(s) the host is connected to.
5. Print out current interface config.
At the present time, the list of Nexus switches to search is hardcoded in the file.

Known Bug: Script currently fails if the results from the arp entry is "incomplete".
