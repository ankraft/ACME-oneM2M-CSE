#
#	TcpServer.py
#
#	(c) 2020 by Andreas Kraft
#	License: BSD 3-Clause License. See the LICENSE file for further details.
#
#	This module contains various utilty functions that are used from various
#	modules and entities of the CSE.
#

class TcpServer(object):

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
		pass

	def close(self):
		pass

	def send(self, p_message):
		pass
