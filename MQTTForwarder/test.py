import logging
import asyncio
import json
import statsd

from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1, QOS_2


STATSD_HOST_ADDRESS   = 'graphical.fake-url.com'

logger = logging.getLogger(__name__)


class PowerParser():
	def __init__(self):
		self.settings = self.__load_settings()
		self.client = MQTTClient()
		self.log = logging.getLogger("Main.PowerParser")

		self.mon_con = statsd.StatsClient(
				host = self.settings['statsd_server'],
				port = 8125,
				prefix = 'PowerStats.SonOff',
				)

	def __load_settings(self):

		with open("conf.json") as fp:
			settings_raw = fp.read()

		conf = json.loads(settings_raw)
		return conf

	def __dispatch_params(self, topic, params_bytes):
		params_str = params_bytes.decode("utf-8")
		if not topic.endswith("/data"):
			self.log.warning("Unknown message! %s => %s" % (topic, params_str))
			return
		params = json.loads(params_str)

		# {
		# 	'current': '3.70',
		# 	'ip': '10.1.2.160',
		# 	'voltage': '119',
		# 	'apparent': '440',
		# 	'energy': '0.81',
		# 	'time': '2017/10/14 07:56:22',
		# 	'power': '386',
		# 	'host': 'SONOFF_POW_0722CA',
		# 	'factor': '87.84',
		# 	'reactive': '210'
		# }

		expect_keys = ['current', 'ip', 'voltage', 'apparent', 'energy', 'time', 'power', 'host', 'factor', 'reactive']
		if not all([key in params for key in expect_keys]):
			self.log.error("Missing key from data!")
			self.log.error("Missing key: %s", [key for key in expect_keys if key not in params])
			self.log.error("Data: %s", params)
			return

		self.log.info("Power message! %s => %s" % (topic, params))

		with self.mon_con.pipeline() as outpipe:
			gaugeprefix = params['host'] + "."
			outpipe.gauge(gaugeprefix + "amps",           float(params['current']))
			outpipe.gauge(gaugeprefix + "voltage",        float(params['voltage']))
			outpipe.gauge(gaugeprefix + "real power",     float(params['power']))
			outpipe.gauge(gaugeprefix + "reactive power", float(params['reactive']))
			outpipe.gauge(gaugeprefix + "apparent power", float(params['apparent']))
			outpipe.gauge(gaugeprefix + "power factor",   float(params['factor']) / 100.0)


	@asyncio.coroutine
	def run(self):

		yield from self.client.connect(self.settings['server'])
		# Subscribe to '$SYS/broker/uptime' with QOS=1
		print("connected")
		yield from self.client.subscribe([
			('/power/#', QOS_1),
		])
		print("subscribed")
		self.log.info("Subscribed")
		while 1:
			try:
				message = yield from self.client.deliver_message()
				packet = message.publish_packet
				self.__dispatch_params(packet.variable_header.topic_name, packet.payload.data)
			except ClientException as ce:
				self.log.error("Client exception: %s" % ce)
			except KeyboardInterrupt:
				break
		yield from self.client.unsubscribe(['$SYS/broker/uptime', '$SYS/broker/load/#'])
		self.log.info("UnSubscribed")
		yield from self.client.disconnect()


if __name__ == '__main__':
	formatter = "[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s"
	logging.basicConfig(level=logging.INFO, format=formatter)
	client = PowerParser()
	asyncio.get_event_loop().run_until_complete(client.run())