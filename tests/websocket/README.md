# WebSocket Tests

This directory contains tests for the CSE's WebSocket binding.
These tests are separated from the normal CSE tests because they require a running WebSocket server to test against.
Also, some of the tests require more fine-grained control over the WebSocket connection than the normal CSE tests.

## Configuration

The file **config.py** contains the configuration for the WebSocket tests. Change the values in this file to match your environment.


## Running the Tests

Each test is a separate file that can be run as follows:

```sh
$ python3 <test_file>.py
```

## Test Cases

### Originator Tests

- **registerAEWithOriginatorReconnect.py**  
	Unit tests for registering an AE with an originator in the WS connection. The connection is closed after the registration and a new connection is opened with the originator. This is the normal case.
- **registerAEWithOriginatorWOReconnect.py**  
	Unit tests for registering an AE with an originator in the WS connection. The connection is NOT closed after the registration and NO new connection	is opened with the originator. This is an error case because the *X-M2M-Origin* header is missing (it cannot be set afterwards in the WS connection).
- **notificationViaSameWS.py**  
	Unit tests for receiving a notification via the same WS connection as the registration. 
- **notificationViaDifferentWS.py**  
	Unit tests for receiving a notification via a different WS connection as the registration. For this the test starts a WS server on a different port to receive the notification.
- **unregisterAEWithDifferentOriginator.py**  
	Unit tests for unregistering an AE with a different originator in the resource as in the WS connection
- **unregisterAEWOOriginator.py**  
	Unit tests for unregistering an AE without an originator in the WS connection. 

