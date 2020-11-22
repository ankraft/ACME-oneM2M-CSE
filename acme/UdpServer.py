

import threading, queue, traceback
from typing import Callable
from Configuration import Configuration
from Logging import Logging

from CoapDissector import CoapMessageRequest, CoapMessageResponse
import socket
# Dtls
import ssl
from dtls.wrapper import wrap_server, wrap_client

class UdpServer(object):

	def __init__(self, p_server_address: str, p_port:str, p_received_data_callback: Callable) -> None:
		self.addr				= p_server_address
		self.port				= p_port
		self.socket				= None # Client socket
		self.listen_socket		= None # Server socket
		self.flag				= False
		self.received_data_callback = p_received_data_callback
		self.useTLS 			= Configuration.get('cse.security.useTLS')
		self.verifyCertificate	= Configuration.get('cse.security.verifyCertificate')
		self.tlsVersion			= Configuration.get('cse.security.tlsVersion').lower()
		self.ssl_version		= { 'tls1.1' : ssl.PROTOCOL_DTLSv1, 'tls1.2' : ssl.PROTOCOL_DTLSv1_2, 'auto' : ssl.PROTOCOL_DTLS }[self.tlsVersion]
		self.caCertificateFile	= Configuration.get('cse.security.caCertificateFile')
		self.caPrivateKeyFile	= Configuration.get('cse.security.caPrivateKeyFile')
		self.privateKeyFile		= Configuration.get('cse.security.privateKeyFile')
		self.certificateFile	= Configuration.get('cse.security.certificateFile')
		self.ssl_ctx			= None
		self.mtu				= 512 #1500

		# End of ctor

	def listen(self, p_timeout:int = 5): # This does NOT return
		self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
		self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		#self.listen_socket.bind((self.addr, self.port))
		#self.listen_socket.settimeout(p_timeout)
		if self.useTLS == True:
			Logging.logDebug('Setup SSL context. CaCertfile: %s, CaKeyFile:%s, Certfile: %s, KeyFile:%s, TLS version: %s' % (self.caCertificateFile, self.caPrivateKeyFile, self.certificateFile, self.privateKeyFile, self.tlsVersion))
			self.ssl_ctx = wrap_server(
				self.listen_socket, 
				keyfile=self.privateKeyFile, 
				certfile=self.certificateFile, 
				cert_reqs=ssl.CERT_NONE if self.verifyCertificate == False else ssl.CERT_REQUIRED, 
				ssl_version=self.ssl_version, 
				ca_certs=self.caCertificateFile, 
				do_handshake_on_connect=True, 
				user_mtu=self.mtu, 
				ssl_logging=True,
				cb_ignore_ssl_exception_in_handshake=None, 
				cb_ignore_ssl_exception_read=None, 
				cb_ignore_ssl_exception_write=None)
			self.ssl_ctx.bind((self.addr, self.port))
			self.ssl_ctx.settimeout(p_timeout)
			self.ssl_ctx.listen(0)
			self.flag = True
			while self.flag:
				Logging.logDebug('UdpServer.listen: In loop: ' + str(self.flag))
				try:
					data, client_address = self.ssl_ctx.recvfrom(4096)
					Logging.logDebug('UdpServer.listen: client_address: ' + str(client_address))
					if len(client_address) > 2:
						client_address = (client_address[0], client_address[1])
					Logging.logDebug('UdpServer.listen: receive_datagram (1) - ' + str(data))
					if not data is None:
						Logging.log('UdpServer.listen: receive_datagram - ' + str(data))
						q = queue.Queue()
						t = threading.Thread(target=self.received_data_callback, args=(data, client_address, q))
						t.setDaemon(True)
						t.start()
						response = q.get()
						self.ssl_ctx.sendto(response)
				except socket.timeout:
					continue
				except Exception as e:
					Logging.logWarn('UdpServer.listen (secure): %s' % str(e))
					continue
				# End of 'while' statement
		else:
			while True:
				try:
					data, client_address = self.listen_socket.recvfrom(4096)
					if len(client_address) > 2:
						client_address = (client_address[0], client_address[1])
					Logging.log('UdpServer.listen: receive_datagram - ' + str(data))
					q = queue.Queue()
					t = threading.Thread(target=self.received_data_callback, args=(data, client_address, q))
					t.setDaemon(True)
					t.start()
					response = q.get()
					self.sendTo(response)
				except socket.timeout:
					continue
				except Exception as e:
					Logging.logWarn('UdpServer.listen: %s' % str(e))
					break
				# End of 'while' statement

			# End of 'while' statement
		# End of method listen

	def _cb_ignore_listen_exception(self, exception, server):
		"""
		In the CoAP server listen method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
		continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.
		:param exception: What happened inside the DTLS stack
		:param server: Reference to the running CoAP server
		:return: True if further processing should be done, False processing should be stopped
		"""
		Logging.log('>>> UdpServer.listen: _cb_ignore_listen_exception: ' + str(exception))
		if isinstance(exception, ssl.SSLError):
			# A client which couldn't verify the server tried to connect, continue but log the event
			if exception.errqueue[-1][0] == ssl.ERR_TLSV1_ALERT_UNKNOWN_CA:
				Logging.logWarn("Ignoring ERR_TLSV1_ALERT_UNKNOWN_CA from client %s" % ('unknown' if not hasattr(exception, 'peer') else str(exception.peer)))
				return True
			# ... and more ...
		return False

	def _cb_ignore_write_exception(self, exception, client):
		"""
		In the CoAP client write method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
		continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.
		note: Default behaviour of CoAPthon without DTLS if no _cb_ignore_write_exception would be called is with "return True"
		:param exception: What happened inside the DTLS stack
		:param client: Reference to the running CoAP client
		:return: True if further processing should be done, False processing should be stopped
		"""
		Logging.log('>>> UdpServer.listen: _cb_ignore_write_exception: ' + str(exception))
		return False

	def _cb_ignore_read_exception(self, exception, client):
		"""
		In the CoAP client read method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
		continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.
		note: Default behaviour of CoAPthon without DTLS if no _cb_ignore_read_exception would be called is with "return False"
		:param exception: What happened inside the DTLS stack
		:param client: Reference to the running CoAP client
		:return: True if further processing should be done, False processing should be stopped
		"""
		Logging.log('>>> UdpServer.listen: _cb_ignore_read_exception: ' + str(exception))
		return False

#	def send(self, p_coapMessage:CoapMessageResponse) -> None:
#		self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#		self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		
	def close(self):
		self.flag = False
		if not self.listen_socket is None:
			self.ssl_ctx.unwrap()
			self.listen_socket.close()
			self.ssl_ctx = None
			self.listen_socket = None
		if not self.socket is None:
			self.socket.close()
			self.socket = None

	def sendTo(self, p_datagram):
		Logging.logDebug('==> UdpServer.sendTo: /%s' % str(p_datagram[1]))
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
			if self.useTLS == True:
				sock = wrap_client(sock, cert_reqs=ssl.CERT_REQUIRED, keyfile=self.privateKeyFile, certfile=self.certificateFile, ca_certs=self.caCertificateFile, do_handshake_on_connect=True, ssl_version=self.ssl_version)
			sock.sendto(p_datagram[0], p_datagram[1])
		except Exception as e:
			Logging.logWarn('UdpServer.sendTo: %s' % str(e))
		finally:
			sock.close()

# End of class UdpServer