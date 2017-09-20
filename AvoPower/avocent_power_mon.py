
import time
import threading
import subprocess
import queue
import statsd
import socket


import pysnmp.hlapi

TARGET_MIBS = {
	# Current wattage for each outlet
	 'w1' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.1')),    #  = INTEGER: 0
	 'w2' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.2')),    #  = INTEGER: 0
	 'w3' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.3')),    #  = INTEGER: 0
	 'w4' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.4')),    #  = INTEGER: 0
	 'w5' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.5')),    #  = INTEGER: 0
	 'w6' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.6')),    #  = INTEGER: 0
	 'w7' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.7')),    #  = INTEGER: 0
	 'w8' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.8')),    #  = INTEGER: 0
	 'w9' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.9')),    #  = INTEGER: 0
	'w10' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.10')),   #  = INTEGER: 0
	'w11' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.11')),   #  = INTEGER: 0
	'w12' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.12')),   #  = INTEGER: 0
	'w13' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.13')),   #  = INTEGER: 0
	'w14' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.14')),   #  = INTEGER: 0
	'w15' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.15')),   #  = INTEGER: 0
	'w16' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.16')),   #  = INTEGER: 0
	'w17' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.17')),   #  = INTEGER: 0
	'w18' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.18')),   #  = INTEGER: 0
	'w19' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.19')),   #  = INTEGER: 0
	'w20' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.5.1.60.1.1.20')),   #  = INTEGER: 0

	# Temperature sensors. Not sure why there's 4
	 't1' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.13.1.20.1.1.1')),   #  = STRING: 20.5oC(68.5oF)
	 't2' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.13.1.21.1.1.1')),   #  = STRING: 21.5oC(71.0oF)
	 't3' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.13.1.22.1.1.1')),   #  = STRING: 20.0oC(68.5oF)
	 't4' : pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('.1.3.6.1.4.1.10418.17.2.5.13.1.23.1.1.1')),   #  = STRING: 20.0oC(68.5oF)
}

class SnmpPoller(object):
	def __init__(self):

		# self.queue = [[pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('IF-MIB', 'ifInOctets', 1))],
		# 		 [pysnmp.hlapi.ObjectType(pysnmp.hlapi.ObjectIdentity('IF-MIB', 'ifOutOctets', 1))]]
		fetch_mibs = [value for value in TARGET_MIBS.values()]
		self.iterator = pysnmp.hlapi.getCmd(pysnmp.hlapi.SnmpEngine(),
					  pysnmp.hlapi.CommunityData(open('community_string.txt').read().strip()),
					  pysnmp.hlapi.UdpTransportTarget(('10.1.1.3', 161)),
					  pysnmp.hlapi.ContextData(),
					  *fetch_mibs)
	def go(self):

		print("Running")
		for errorIndication, errorStatus, errorIndex, varBinds in self.iterator:
			if errorIndication:
				print(errorIndication)
			elif errorStatus:
				print('%s at %s' % (errorStatus.prettyPrint(),
									errorIndex and varBinds[int(errorIndex) - 1][0] or '?'))
			else:
				for varBind in varBinds:
					print(' = '.join([x.prettyPrint() for x in varBind]))


# STATSD_HOST_ADDRESS = 'graphical.fake-url.com'

# HEADER_LINE = ['NAME', 'STATE', 'CPU(sec)', 'CPU(%)', 'MEM(k)', 'MEM(%)', 'MAXMEM(k)',
# 			'MAXMEM(%)', 'VCPUS', 'NETS', 'NETTX(k)', 'NETRX(k)', 'VBDS',
# 			'VBD_OO', 'VBD_RD', 'VBD_WR', 'VBD_RSECT', 'VBD_WSECT', 'SSID']

# COL_KEYS = [None, 'CPU_sec', 'CPU_percent', 'MEM_k', 'MEM_percent', None,
# 			None, 'VCPUs', 'Networks', 'NET-TX_k', 'NET-RX_k', 'Block-Devices',
# 			None, 'VBD_Read', 'VBD_Write', 'VBD_Read-Sectors', 'VBD_Write-Sectors', None]

# class AsyncLineReader(threading.Thread):
# 	def __init__(self, fd, outputQueue):
# 		threading.Thread.__init__(self)

# 		assert isinstance(outputQueue, queue.Queue)
# 		assert callable(fd.readline)

# 		self.fd = fd
# 		self.outputQueue = outputQueue

# 	def run(self):
# 		for item in iter(self.fd.readline, b''):
# 			self.outputQueue.put(item)
# 		print("AsyncLineReader finished!")
# 		print("FD: ", self.fd)


# 	def eof(self):
# 		return not self.is_alive() and self.outputQueue.empty()

# 	@classmethod
# 	def getForFd(cls, fd, start=True):
# 		out_queue = queue.Queue()
# 		reader = cls(fd, out_queue)

# 		if start:
# 			reader.start()

# 		return reader, out_queue

# class XenMonitor(object):
# 	def __init__(self):
# 		command = ["sudo xentop -b -f -d2"]

# 		self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

# 		self.stdoutReader, self.stdoutQueue = AsyncLineReader.getForFd(self.process.stdout)
# 		self.stderrReader, self.stderrQueue = AsyncLineReader.getForFd(self.process.stderr)

# 		self.alive = True
# 		hostclean = socket.gethostname().replace(".", "_")

# 		self.mon_con = statsd.StatsClient(
# 				host = STATSD_HOST_ADDRESS,
# 				port = 8125,
# 				prefix = 'XenVms.'+hostclean,
# 				)


# 	def run(self):

# 		# Keep checking queues until there is no more output.
# 		while self.alive and (not self.stdoutReader.eof() or not self.stderrReader.eof()):
# 			# Process all available lines from the stdout Queue.
# 			while not self.stdoutQueue.empty():
# 				line = self.stdoutQueue.get()
# 				self.process_stdout_line(line.decode("ascii"))

# 				# Do stuff with stdout line.

# 			# Process all available lines from the stderr Queue.
# 			while not self.stderrQueue.empty():
# 				line = self.stderrQueue.get()
# 				print('Received stderr: ' + repr(line))

# 				# Do stuff with stderr line.
# 			# print("Looping!")
# 			# Sleep for a short time to avoid excessive CPU use while waiting for data.
# 			time.sleep(0.5)

# 	def process_stdout_line(self, line):
# 		line = line.strip()
# 		while "  " in line:
# 			line = line.replace("  ", " ")
# 		line = line.split(" ")
# 		if len(line) != 19:
# 			return

# 		# Skip the header line
# 		if line == HEADER_LINE:
# 			# print("Header line!")
# 			return

# 		vmname = line.pop(0)
# 		vmname = vmname.replace(".", "-")
# 		if vmname == "Domain-0":
# 			vmname = vmname + "-" + socket.gethostname().replace(".", "-")

# 		with self.mon_con.pipeline() as outpipe:
# 			for key, value in zip(COL_KEYS, line):
# 				if not key:
# 					continue
# 				value = float(value)
# 				outpipe.gauge(key + "." + vmname, value)


# 	def close(self):
# 		self.alive = False


# 		print("Waiting for async readers to finish...")
# 		self.stdoutReader.join()
# 		self.stderrReader.join()

# 		# Close subprocess' file descriptors.
# 		self.process.stdout.close()
# 		self.process.stderr.close()

# 		print("Waiting for process to exit...")
# 		returnCode = self.process.wait()

# 		if returnCode != 0:
# 			raise subprocess.CalledProcessError(returnCode, command)


def go():
	mon = SnmpPoller()
	mon.go()

if __name__ == '__main__':
	go()

