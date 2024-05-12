# Experimental WebSocket Binding

In release 2024.03 the ACME CSE got support for the WebSocket protocol. This protocol offers an always-on connection between a client and a server for fast data transfer. The performance gain comes mostly from the fact that with WebSockets it is not necessary to establish new network connections, opening sockets etc. every time when a request is sent.

This binding is especially useful for CSE-to-CSE connections when two CSEs are constantly exchanging requests and responses. However, it is not really suited for devices (ADN) to use this protocol binding because the drawback is that computing and network resources are kept constantly assigned by both parties. It may make sense, though, to support this binding on an ADN whenever the use case is bulk and high frequency transfer of requests, such in the case of time series data.

## WebSocket and Originators

The technical specification is published in oneM2M's TS-0020 and available [on the specification page](https://onem2m.org/technical/published-specifications) . Unfortunately, there is a small issue in the specification when it comes to send notifications from, for example, a CSE to a connected AE or CSE. 

The specification states that an established WebSocket connection must be used when sending notifications to a client (an AE or CSE). In normal cases, this is not a problem. However, there could be a situation that a client establishes a WebSocket connection but doesn't send a request immediately. This is normal behavior, but without a oneM2M request the CSE cannot associate that specific WebSocket connection with an originator. If in this case the CSE needs to send a notification to a client (ie. an originator) it does not know whether there is an established WebSocket connection, even if, technically, there is one.

The solution for this is that a client needs to add an additional header when opening a WebSocket connection. This is similar to the `X-M2M-Origin` header in the oneM2M HTTP binding, and in fact the experimental feature proposes that this header must be present when a WebSocket connection is opened. 

```python title="Example Python Code"
websocket = connect(cseUrl, 
					subprotocols=['oneM2M.json'],
					additional_headers={ 'X-M2M-Origin': anOriginator })
```

The only exception is when registering an AE. In this case, again similar to the HTTP binding, this header may be absent. 

## Establishing WebSocket Connections

Another experimental feature is that WebSockets may be established from AEs as well as CSE's (or *registrees* and *registrars* in oneM2M terms). The original (current) specification states that WebSockets must only be established by a *registree*, but this is very limiting and may force small ADN devices to implement multiple oneM2M bindings technologies when they want to be able to receive notifications even when no WebSocket connection has been established. Also, it is not clearly specified how to store requests from a *registrar* to a *registree* in case a connection is not available at the moment.

The implemented experimental feature now adds the following procedure and a special URL schema for the *poa* (point of access) attribute for WebSocket connections:

- If there is an established WebSocket connection for a request originator then send the request over this connection.
- If there is no established WebSocket connection:
  1. If there is a URL in the *poa* attribute with the value `ws://default` then don't open a new WebSocket connection (because only the default one should be used). Continue with step iii.
  2. If there is a "normal" WebSocket URL then establish a WebSocket connection to that URL and send the request and await the response. Afterwards the connection may be closed.
  3. Otherwise follow the usual procedure for *poa* handling, ie. look for other means to reach the originator.

To support this feature, of course, a *registree* must implement a WebSocket server as well.

## Changes to oneM2M's TS-0020 WebSocket Binding Specification

These changes were submitted as a Change Request *SDS-2024-0021* to TS-0020 (March 2024) and will be discussed in oneM2M's SDS working group.