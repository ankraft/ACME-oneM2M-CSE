//
// rest.js
//
// (c) 2020 by Andreas Kraft
// License: BSD 3-Clause License. See the LICENSE file for further details.
//
// Javascript Mca functions
//


var HttpClient = function() {
  this.get = function(id, node, callback, errorCallback) {
    sendRetrieveRequest(node, id, originator, callback, errorCallback )
  }

  this.delete = function(id, node, callback, errorCallback) {
    sendDeleteRequest(node, id, originator, callback, errorCallback )
  }

  // TODO: do we really need a separate method?
  this.getChildren = function(id, node, callback, errorCallback) {
    sendRetrieveRequest(node, id, originator, callback, errorCallback)
  }
}


function sendRetrieveRequest(node, id, originator, callback, errorCallback) {
  sendRequest("GET", node, id, originator, callback, errorCallback)
}


function sendDeleteRequest(node, id, originator, callback, errorCallback) {
  sendRequest("DELETE", node, id, originator, callback, errorCallback)
}


function sendRequest(method, node, url, originator, callback, errorCallback) {
  var request = new XMLHttpRequest();

  request.onreadystatechange = function() { 
    if (request.readyState == 4) {
      if (request.status == 200) {
        callback(request.responseText, node);
      } else {
        typeof errorCallback === 'function' && errorCallback(request.responseText, request.status);
      }
    }
  }

  // Translate SP-relative an address to HTTP repesentation
  if (url.charAt(0) == '/') {
  	url = '~' + url;
  }

  request.open(method, "/"+url, true );     
  request.setRequestHeader("X-M2M-Origin", originator);
  request.setRequestHeader("Accept", "application/json");
  request.setRequestHeader("X-M2M-RI", "123");       
  request.setRequestHeader("X-M2M-RVI", "3");       
  request.send(null);
}


function getTextFromServer(path, callback) {
  var client = new XMLHttpRequest();
  client.open('GET', path);
  client.onreadystatechange = function() {
    callback(client.responseText)
  }
  client.send();
}
