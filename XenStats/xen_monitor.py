
import time
import threading
import subprocess
import queue
import statsd
import socket

STATSD_HOST_ADDRESS = 'graphical.fake-url.com'

HEADER_LINE = ['NAME', 'STATE', 'CPU(sec)', 'CPU(%)', 'MEM(k)', 'MEM(%)', 'MAXMEM(k)',
			'MAXMEM(%)', 'VCPUS', 'NETS', 'NETTX(k)', 'NETRX(k)', 'VBDS',
			'VBD_OO', 'VBD_RD', 'VBD_WR', 'VBD_RSECT', 'VBD_WSECT', 'SSID']

COL_KEYS = [None, 'CPU_sec', 'CPU_percent', 'MEM_k', 'MEM_percent', None,
			None, 'VCPUs', 'Networks', 'NET-TX_k', 'NET-RX_k', 'Block-Devices',
			None, 'VBD_Read', 'VBD_Write', 'VBD_Read-Sectors', 'VBD_Write-Sectors', None]

class AsyncLineReader(threading.Thread):
	def __init__(self, fd, outputQueue):
		threading.Thread.__init__(self)

		assert isinstance(outputQueue, queue.Queue)
		assert callable(fd.readline)

		self.fd = fd
		self.outputQueue = outputQueue

	def run(self):
		for item in iter(self.fd.readline, b''):
			self.outputQueue.put(item)
		print("AsyncLineReader finished!")
		print("FD: ", self.fd)


	def eof(self):
		return not self.is_alive() and self.outputQueue.empty()

	@classmethod
	def getForFd(cls, fd, start=True):
		out_queue = queue.Queue()
		reader = cls(fd, out_queue)

		if start:
			reader.start()

		return reader, out_queue

class XenMonitor(object):
	def __init__(self):
		command = ["sudo xentop -b -f -d2"]

		self.process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		self.stdoutReader, self.stdoutQueue = AsyncLineReader.getForFd(self.process.stdout)
		self.stderrReader, self.stderrQueue = AsyncLineReader.getForFd(self.process.stderr)

		self.alive = True
		hostclean = socket.gethostname().replace(".", "_")

		self.mon_con = statsd.StatsClient(
				host = STATSD_HOST_ADDRESS,
				port = 8125,
				prefix = 'XenVms.'+hostclean,
				)


	def run(self):

		# Keep checking queues until there is no more output.
		while self.alive and (not self.stdoutReader.eof() or not self.stderrReader.eof()):
			# Process all available lines from the stdout Queue.
			while not self.stdoutQueue.empty():
				line = self.stdoutQueue.get()
				self.process_stdout_line(line.decode("ascii"))

				# Do stuff with stdout line.

			# Process all available lines from the stderr Queue.
			while not self.stderrQueue.empty():
				line = self.stderrQueue.get()
				print('Received stderr: ' + repr(line))

				# Do stuff with stderr line.
			# print("Looping!")
			# Sleep for a short time to avoid excessive CPU use while waiting for data.
			time.sleep(0.5)

	def process_stdout_line(self, line):
		line = line.strip()
		while "  " in line:
			line = line.replace("  ", " ")
		line = line.split(" ")
		if len(line) != 19:
			return

		# Skip the header line
		if line == HEADER_LINE:
			# print("Header line!")
			return

		vmname = line.pop(0)
		vmname = vmname.replace(".", "-")
		if vmname == "Domain-0":
			vmname = vmname + "-" + socket.gethostname().replace(".", "-")

		with self.mon_con.pipeline() as outpipe:
			for key, value in zip(COL_KEYS, line):
				if not key:
					continue
				value = float(value)
				outpipe.gauge(key + "." + vmname, value)


	def close(self):
		self.alive = False


		print("Waiting for async readers to finish...")
		self.stdoutReader.join()
		self.stderrReader.join()

		# Close subprocess' file descriptors.
		self.process.stdout.close()
		self.process.stderr.close()

		print("Waiting for process to exit...")
		returnCode = self.process.wait()

		if returnCode != 0:
			raise subprocess.CalledProcessError(returnCode, command)


def go():
	mon = XenMonitor()
	mon.run()
	mon.close()

if __name__ == '__main__':
	go()

