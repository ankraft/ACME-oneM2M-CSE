#
#	mqttTestDirectURL.py
#
#	(c) 2024 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	Test case for registering an AE, CNT and SUB and receiving a notification via a direct MQTT 
#	connection.

import paho.mqtt.client as mqtt
import threading, time, random, json, sys, urllib.parse
from rich import print

# Configurations

# MQTT Broker
mqttHost = "mqtt"
mqttPort = 1883
mqttUser = "test"
mqttPassword = "mqtt"

CSEID = 'id-in'
CSERN = 'cse-in'
ORIGINATOR = 'CmqttTest'


MQTTREQUESTTOPIC	= f'/oneM2M/req/{ORIGINATOR}/{CSEID}/json'
MQTTRESPONSETOPIC	= f'/oneM2M/resp/{ORIGINATOR}/{CSEID}/json'
MQTTREGREQUESTTOPIC	= f'/oneM2M/reg_req/anMqttClient/{CSEID}/json'
MQTTREGRESPONSETOPIC= f'/oneM2M/reg_resp/anMqttClient/{CSEID}/json'

FUNNYTOPIC = f'%2fbla'	# /bla

_message:dict = {}
_notification:dict = {}
_rsc:int = 0
_originator = 'C'

def _uniqueID() -> str:
	""" Create a unique ID.

		Returns:
			A unique ID.
	"""
	return str(random.randint(1,sys.maxsize))


def clear_message() -> None:
	""" Clear the message dictionary.
	"""
	global _message, _rsc, _notification
	_message = {}
	_notification = {}
	_rsc = 0


def on_connect(client, userdata, flags, rc):
	print(f'MQTT: Connected with result code {str(rc)}')
	print(f'MQTT: Subscribing to {MQTTRESPONSETOPIC}')
	client.subscribe(MQTTRESPONSETOPIC)
	print(f'MQTT: Subscribing to {MQTTREGRESPONSETOPIC}')
	client.subscribe(MQTTREGRESPONSETOPIC)
	print(f'MQTT: Subscribing to {urllib.parse.unquote(FUNNYTOPIC)}')
	client.subscribe(urllib.parse.unquote(FUNNYTOPIC))
				  

def on_disconnect(client, userdata, rc):
	print(f'MQTT: Disconnected with result code {str(rc)}')


def on_subscribe(client, userdata, mid, granted_qos):
	print('MQTT: Subscribed to topic')


def on_message(client, userdata, msg):
	global _rsc, _message, _notification
	_message = json.loads(msg.payload)
	if _message.get('op') == 5:
		_notification = _message
		print(f'[green1]MQTT Notification received:[/green1] {msg.topic}\n{_notification}')
		_message = {}
	else:
		print(f'[green1]MQTT Received:[/green1] {msg.topic}\n{str(msg.payload.decode())}')
		_rsc = _message.get('rsc')


def wait_for_message() -> dict:
	# wait until the response is received or a timeout occurs
	timeout = 10
	start = time.time()
	while time.time() < start + timeout:
		if _message or _notification:
			break
		else:
			print("waiting")
			time.sleep(1)
	else:
		raise TimeoutError('Timeout waiting for message')


def send_message(client:mqtt.Client, topic:str, message:dict) -> None:
	_request = json.dumps(message)
	print(f'[orange1]MQTT sent:[/orange1] {topic}\n{_request}')
	client.publish(topic, _request)


if __name__ == '__main__':
	client = mqtt.Client()
	client.on_connect = on_connect
	client.on_disconnect = on_disconnect
	client.on_message = on_message
	client.on_subscribe = on_subscribe

	if mqttUser and mqttPassword:
		client.username_pw_set(mqttUser, mqttPassword)  # Set username and password

	client.connect(mqttHost, mqttPort, 60)
	client.loop_start()
	time.sleep(2)  # Wait for the connection to establish

	#
	# register AE
	#
	print('\n[blue]Registering AE[/blue]')
	request = {
		'to': CSERN,
		'fr': ORIGINATOR,
		'op': 1,
		'rqi': _uniqueID(),
		'rvi': '4',
		'ty': 2,
		'pc': {
			'm2m:ae': {
				'api': 'NmyApp',
				'rr': True,
				'rn': 'myAE',
				'srv': [ '3', '4' ],
			}}
	}
	try:
		clear_message()
		send_message(client, MQTTREGREQUESTTOPIC, request)
		wait_for_message()
		if _rsc != 2001:
			raise Exception(f'Error registering AE: {_message}')
	except Exception as e:
		print(e)
		sys.exit(1)


	#
	#	create SUB
	#
	print('\n[blue]Creating SUB[/blue]')
	request = {
		'to': f'{CSERN}/myAE',
		'fr': ORIGINATOR,
		'op': 1,
		'rqi': _uniqueID(),
		'rvi': '4',
		'ty': 23,
		'pc': {
			'm2m:sub': {
				'rn': 'mySub',
				'enc': {
					'net': [ 1 ]
				},
				'nu': [ f'mqtt://{mqttHost}:{mqttPort}/{FUNNYTOPIC}' ],
				'nct': 1
			}
		}
	}
	try:
		clear_message()
		send_message(client, MQTTREQUESTTOPIC, request)
		while not _message: # wait until the response is received, ignore notifications
			wait_for_message()
		if _rsc != 2001:
			raise Exception(f'Error creating SUB: {_message}')
	except TimeoutError as e:
		print(e)
		sys.exit(1)
		

	#
	# unregister AE
	#
	request = {
		'to': f'{CSERN}/myAE',
		'fr': ORIGINATOR,
		'op': 4,
		'rqi': _uniqueID(),
		'rvi': '4'
	}
	print('\n[blue]Unregistering AE[/blue]')
	try:
		clear_message()
		send_message(client, MQTTREQUESTTOPIC, request)
		wait_for_message()
		if _rsc != 2002:
			raise Exception(f'Error unregistering AE: {_message}')
	except TimeoutError as e:
		print(e)
		sys.exit(1)


	print('\n[blue]Finishing & shutting down[/blue]')

	time.sleep(2)  # Wait for settling down

	client.disconnect()
	client.loop_stop(True)