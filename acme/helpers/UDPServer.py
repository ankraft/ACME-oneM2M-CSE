#
#	UdpServer.py
#
#	(c) 2023 by Andreas Kraft, Yann Garcia
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

import threading
from typing import Callable, Any, Tuple
import socket
# Dtls
import ssl
from dtls.wrapper import wrap_server, wrap_client, DtlsSocket
import dtls.sslconnection as sslconnection

from ..helpers.BackgroundWorker import BackgroundWorkerPool

class UdpServer(object):

	__slots__ = (
		'addr', 
		'port', 
		'socket', 
		'listen_socket', 
		'doListen', 
		'received_data_callback', 
		'useTLS', 
		'verifyCertificate', 
		'tlsVersion', 
		'ssl_version', 
		'privateKeyFile', 
		'certificateFile', 
		'privateKeyFile',
		'certificateFile',
		'logging',
		'ssl_ctx',
		'mtu'
	)

	def __init__(self, server_address:str,
	      			   port:str,
					   useDTLS:bool,
					   tlsVersion:str,
					   verifyCertificate:bool,
					   privateKeyFile:str,
					   certificateFile:str,
					   received_data_callback:Callable,
					   logging:Callable) -> None:
		self.addr = server_address
		self.port = port
		self.socket:socket.socket = None # Client socket
		self.listen_socket:socket.socket = None # Server socket
		self.doListen = False
		self.received_data_callback = received_data_callback
		self.useTLS = useDTLS
		self.tlsVersion = tlsVersion
		self.ssl_version = { 'tls1.1': sslconnection.PROTOCOL_DTLSv1, 
		       				 'tls1.2': sslconnection.PROTOCOL_DTLSv1_2, 
							 'auto': sslconnection.PROTOCOL_DTLS }[self.tlsVersion]
		self.verifyCertificate	= verifyCertificate

		self.privateKeyFile = privateKeyFile
		self.certificateFile = certificateFile
		self.logging = logging
		self.ssl_ctx:DtlsSocket	= None
		self.mtu = 512 #1500 TODO configurable	


	def listen(self, timeout:int = 5) -> None: # This does NOT return
		self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


		def _listen(listenSocket:Tuple[socket.socket, DtlsSocket]) -> None:
			self.doListen = True
			while self.doListen:
				self.logging(f'UdpServer.listen: In loop: {str(self.doListen)}')
				try:
					data, client_address = listenSocket.recvfrom(4096)
					self.logging(f'UdpServer.listen: client_address: {str(client_address)}')
					if len(client_address) > 2:
						client_address = (client_address[0], client_address[1])
					self.logging(f'UdpServer.listen: receive_datagram (1) - {str(data)}')
					if data is not None:
						self.logging(f'UdpServer.listen: receive_datagram - - {str(data)}')
						BackgroundWorkerPool.runJob(lambda : self.received_data_callback(data, client_address), f'CoAP_{str(client_address)}')	# TODO a better thread name
						# t = threading.Thread(target=self.received_data_callback, args=(data, client_address))
						# t.setDaemon(True)
						# t.start()
				except socket.timeout:
					continue
				except Exception as e:
					self.logging(f'UdpServer.listen (secure): {str(e)}')
					continue


		if self.useTLS == True:

			# Setup DTLS context
			self.logging(f'Setup SSL context. Certfile: {self.certificateFile}, KeyFile: {self.privateKeyFile}, TLS version: {self.tlsVersion}')
			self.ssl_ctx = wrap_server(
				self.listen_socket, 
				keyfile = self.privateKeyFile, 
				certfile = self.certificateFile, 
				cert_reqs = ssl.CERT_NONE if self.verifyCertificate == False else ssl.CERT_REQUIRED, 
				ssl_version = self.ssl_version, 
				#ca_certs=self.caCertificateFile, 
				do_handshake_on_connect = True, 
				user_mtu = self.mtu, 
				ssl_logging = True,
				cb_ignore_ssl_exception_in_handshake = None, 
				cb_ignore_ssl_exception_read = None, 
				cb_ignore_ssl_exception_write = None)
			
			# Initialize and start listening
			self.ssl_ctx.bind((self.addr, self.port))
			self.ssl_ctx.settimeout(timeout)
			self.ssl_ctx.listen(0)
			_listen(self.ssl_ctx)	# Does not return
			# self.doListen = True
			# while self.doListen:
			# 	self.logging(f'UdpServer.listen: In loop: {str(self.doListen)}')
			# 	try:
			# 		data, client_address = self.ssl_ctx.recvfrom(4096)
			# 		self.logging(f'UdpServer.listen: client_address: {str(client_address)}')
			# 		if len(client_address) > 2:
			# 			client_address = (client_address[0], client_address[1])
			# 		self.logging(f'UdpServer.listen: receive_datagram (1) - {str(data)}')
			# 		if not data is None:
			# 			self.logging(f'UdpServer.listen: receive_datagram - - {str(data)}')
			# 			BackgroundWorkerPool.runJob(lambda : self.received_data_callback(data, client_address), f'CoAP_{str(client_address)}')	# TODO a better thread name
			# 			# t = threading.Thread(target=self.received_data_callback, args=(data, client_address))
			# 			# t.setDaemon(True)
			# 			# t.start()
			# 	except socket.timeout:
			# 		continue
			# 	except Exception as e:
			# 		self.logging(f'UdpServer.listen (secure): {str(e)}')
			# 		continue

		else:
			# Initialize and start listening (non-secure)
			self.listen_socket.bind((self.addr, self.port))
			self.listen_socket.settimeout(timeout)
			_listen(self.listen_socket)	# Does not return

			# self.doListen = True
			# while self.doListen:
			# 	try:
			# 		data, client_address = self.listen_socket.recvfrom(4096)
			# 		if len(client_address) > 2:
			# 			client_address = (client_address[0], client_address[1])
			# 		Logging.log(f'UdpServer.listen: receive_datagram - {str(data)}')
			# 		t = threading.Thread(target=self.received_data_callback, args=(data, client_address))
			# 		t.setDaemon(True)
			# 		t.start()
			# 	except socket.timeout:
			# 		continue
			# 	except Exception as e:
			# 		Logging.logWarn(f'UdpServer.listen: {str(e)}')
			# 		break


	# # def _cb_ignore_listen_exception(self, exception, server):
	# 	"""
	# 	In the CoAP server listen method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
	# 	continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.
	# 	:param exception: What happened inside the DTLS stack
	# 	:param server: Reference to the running CoAP server
	# 	:return: True if further processing should be done, False processing should be stopped
	# 	"""
	# 	Logging.log('>>> UdpServer.listen: _cb_ignore_listen_exception: ' + str(exception))
	# 	if isinstance(exception, ssl.SSLError):
	# 		# A client which couldn't verify the server tried to connect, continue but log the event
	# 		if exception.errqueue[-1][0] == ssl.ERR_TLSV1_ALERT_UNKNOWN_CA:
	# 			Logging.logWarn("Ignoring ERR_TLSV1_ALERT_UNKNOWN_CA from client %s" % ('unknown' if not hasattr(exception, 'peer') else str(exception.peer)))
	# 			return True
	# 		# ... and more ...
	# 	return False

	# def _cb_ignore_write_exception(self, exception, client):
	# 	"""
	# 	In the CoAP client write method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
	# 	continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.
	# 	note: Default behaviour of CoAPthon without DTLS if no _cb_ignore_write_exception would be called is with "return True"
	# 	:param exception: What happened inside the DTLS stack
	# 	:param client: Reference to the running CoAP client
	# 	:return: True if further processing should be done, False processing should be stopped
	# 	"""
	# 	Logging.log('>>> UdpServer.listen: _cb_ignore_write_exception: ' + str(exception))
	# 	return False

	# def _cb_ignore_read_exception(self, exception, client) -> bool:
	# 	"""	In the CoAP client read method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
	# 		continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.
	# 		note: Default behaviour of CoAPthon without DTLS if no _cb_ignore_read_exception would be called is with "return False"

	# 		Args:
	# 			exception: What happened inside the DTLS stack.
	# 			client: Reference to the running CoAP client.
			
	# 		Returns:
	# 			True if further processing should be done, False processing should be stopped
	# 	"""
	# 	Logging.log('>>> UdpServer.listen: _cb_ignore_read_exception: ' + str(exception))
	# 	return False

#	def send(self, p_coapMessage:CoapMessageResponse) -> None:
#		self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
	def close(self) -> None:
		self.doListen = False
		if self.listen_socket:
			if self.ssl_ctx:
				self.ssl_ctx.unwrap()
			self.listen_socket.close()
			self.ssl_ctx = None
			self.listen_socket = None
		if self.socket:
			self.socket.close()
			self.socket = None


	def sendTo(self, datagram):
		self.logging(f'==> UdpServer.sendTo: /{str(datagram[0])} - {str(datagram[1])}')
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			if self.useTLS == True:
				sock = wrap_client(sock, cert_reqs = ssl.CERT_REQUIRED, 
		       							 keyfile = self.privateKeyFile, 
										 certfile = self.certificateFile, 
										 ca_certs = self.caCertificateFile, 
										 do_handshake_on_connect = True, 
										 ssl_version = self.ssl_version)
			sock.sendto(datagram[0], datagram[1])
		except Exception as e:
			self.logging(f'UdpServer.sendTo: {str(e)}')
		finally:
			sock.close()
