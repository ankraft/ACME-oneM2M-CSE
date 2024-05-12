# Certificates

The ACME CSE supports the secure protocol version of HTTP, MQTT, and WebSockets. This means that you can use the CSE with HTTPS, MQTT over TLS, and WSS.

To enable, for example, https you have to set various settings under the security configuration [http.security](../setup/Configuration-http.md#security), and provide a certificate and a key file. The other protocols are configured in a similar way.

!!! see-also "See also"
	[HTTP Security Settings](../setup/Configuration-http.md#security)  
	[MQTT Security Settings](../setup/Configuration-mqtt.md#security)  
	[WebSocket Security Settings](../setup/Configuration-ws.md#security)

## Self-Signed Certificates

One way to create those files is the [openssl](https://www.openssl.org){target=_new} tool that may already be installed on your OS. The following example shows how to create a self-signed certificate:

```bash title="Create a self-signed certificate"
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -nodes -days 1000
```

This will create the self-signed certificate and private key without password protection (*-nodes*), and stores them in the files *cert.pem* and *key.pem* respectively. *openssl* will prompt you with questions for *Country Name* etc, but you can just hit *Enter* and accept the defaults. The *-days* parameter affects the certificate's expiration date.

Please also consult the *openssl* manual for further instructions. 

After you generated these files you can move them to a separate directory (for example you may create a new directory named *cert* under ACME's [runtime base directory](../setup/Running.md#different-base-directory)) and set the *caCertificateFile* and *caPrivateKeyFile* configuration parameters in the *acme.ini* configuration file under the appropriate security section(s) accordingly.
