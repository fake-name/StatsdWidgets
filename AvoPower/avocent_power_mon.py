
import time
import threading
import subprocess
import queue
import statsd
import socket
import traceback

import pysnmp.hlapi

STATSD_HOST_ADDRESS   = 'graphical.fake-url.com'
PDU_DEVICE_ADDRESS    = '10.1.1.3'
SNMP_COMMUNITY_STRING = open('/usr/local/bin/community_string.txt').read().strip()


TARGET_MIBS = {
	# Bank voltages
	 'v1' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.11.1.70.1.1.1'),    #  = INTEGER: 0
	 'v2' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.11.1.70.1.1.2'),    #  = INTEGER: 0
	# Bank power consumption
	'bw1' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.11.1.60.1.1.1'),    #  = INTEGER: 0
	'bw2' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.11.1.60.1.1.2'),    #  = INTEGER: 0
	# Current wattage for each outlet

	 'w1' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.1'),    #  = INTEGER: 0
	 'w2' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.2'),    #  = INTEGER: 0
	 'w3' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.3'),    #  = INTEGER: 0
	 'w4' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.4'),    #  = INTEGER: 0
	 'w5' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.5'),    #  = INTEGER: 0
	 'w6' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.6'),    #  = INTEGER: 0
	 'w7' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.7'),    #  = INTEGER: 0
	 'w8' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.8'),    #  = INTEGER: 0
	 'w9' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.9'),    #  = INTEGER: 0
	'w10' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.10'),   #  = INTEGER: 0
	'w11' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.11'),   #  = INTEGER: 0
	'w12' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.12'),   #  = INTEGER: 0
	'w13' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.13'),   #  = INTEGER: 0
	'w14' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.14'),   #  = INTEGER: 0
	'w15' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.15'),   #  = INTEGER: 0
	'w16' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.16'),   #  = INTEGER: 0
	'w17' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.17'),   #  = INTEGER: 0
	'w18' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.18'),   #  = INTEGER: 0
	'w19' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.19'),   #  = INTEGER: 0
	'w20' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.20'),   #  = INTEGER: 0

	# Temperature sensors. Not sure why there's 4
	 't1' : pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.13.1.25.1.1.1'),   #  = deg f * 10
}
# INVERSE_MIB_MAP = {
# 	val : key for key, val in TARGET_MIBS.items()
# }

class SnmpPoller(object):
	def __init__(self):
		self.mon_con = statsd.StatsClient(
				host = STATSD_HOST_ADDRESS,
				port = 8125,
				prefix = 'PowerStats.SnmpPoller.AvocentPDU',
				)

	def poll(self):
		vals = {}
		fetch_mibs = [pysnmp.hlapi.ObjectType(value) for value in TARGET_MIBS.values()]
		iterator = pysnmp.hlapi.getCmd(pysnmp.hlapi.SnmpEngine(),
					  pysnmp.hlapi.CommunityData(SNMP_COMMUNITY_STRING),
					  pysnmp.hlapi.UdpTransportTarget((PDU_DEVICE_ADDRESS, 161)),
					  pysnmp.hlapi.ContextData(),
					  *fetch_mibs)

		for errorIndication, errorStatus, errorIndex, varBinds in iterator:
			if errorIndication:
				print(errorIndication)
			elif errorStatus:
				print('%s at %s' % (errorStatus.prettyPrint(),
									errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				for varBind in varBinds:
					# print("Varbind: ", varBind)
					# print("Val:", [x for x in varBind])
					oid, value = varBind
					for key, tgt in TARGET_MIBS.items():
						if tgt == oid:

							try:
								vals[key] = float(value)
								if 'w' in key:
									# Values seem to generally be int(val * 10)
									vals[key] = vals[key] / 10
							except ValueError:
								pass
		print("Shipping stats")
		with self.mon_con.pipeline() as outpipe:
			for key, value in vals.items():
				outpipe.gauge(key, value)


	def go(self):
		while 1:
			try:
				self.poll()
			except Exception:
				print("Failure during poll!")
				traceback.print_exc()
			time.sleep(5)
			# import pdb
			# pdb.set_trace()


def go():
	mon = SnmpPoller()
	mon.go()

if __name__ == '__main__':
	go()

