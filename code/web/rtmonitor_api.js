"use strict"
/* JS Socket code to access RTMonitor real-time sirivm data */
//
function RTMonitorAPI(client_data, optional_uri) {

var VERSION = '3.41';
// 3.41 added re-use of existing socket to avoid multiple socket connections from same client
// 3.4  token support, set_uri method
// 3.3  added raw() and request() methods to rtmonitor api client (for rtroute.js)
// 3.2  only connect to server when first client connects, disconnect from server after last client calls close()
// 3.1  restructure of rtmonitor API, .register(..) returns api object (.connect, .subscribe, .unsubscribe)
// 3.0  move most this.X -> var X
// 2.0  restructure to Object + methods
// 1.0  initial working version RTMonitor JS Proxy
//
// client_data will passed to rt_monitor at connect time
// to help identify/validate the client.
// client_data = { rt_client_id: <unique id for this client>
//                 rt_client_name: <some descriptive name, e.g. display name>
//                 rt_client_url: <location.href of this connecting web page client>
//                 rt_token: <token to be passed to rt_monitor in the connection to validate>
//               }

var RTMONITOR_URI = optional_uri ? optional_uri : 'https://smartcambridge.org/rtmonitor/sirivm';
//this.RTMONITOR_URI = 'https://tfc-app2.cl.cam.ac.uk/rtmonitor/sirivm';
//this.RTMONITOR_URI = 'http://tfc-app2.cl.cam.ac.uk/test/rtmonitor/sirivm';

if (!optional_uri)
{
    console.log('RTMonitorAPI', 'WARN - instantiated without a RTMonitor URI, using smartcambridge');
}

var self = this;

//var DEBUG = 'rtmonitor_api_log';

if (client_data)
{
    self.client_data = client_data;
}
else
{
    self.client_data = {};
    self.client_data.rt_client_id = 'unknown';
    self.client_data.rt_token = 'unknown';
    self.client_data.rt_client_name = 'rtmonitor_api.js V'+VERSION;
}
self.client_data.rt_client_url = location.href;
self.client_data.rt_version = VERSION;

log('RTMonitorAPI V'+VERSION+' instantiation',self.client_data);

var sock = null; // the page's WebSocket

var sock_timer = {}; // intervalTimer we use for retries if socket has failed

var revive = true; // "Resuscitate" flag, 'true' enables 'reconnect' in sock.onclose callback

var requests = {}; // dictionary of request_id -> callback_function for requests and subscriptions

// rt_connection_status - disconnected .. connecting .. connected
var rt_connection_status = 'disconnected'; // whether the websocket is connected or not


var clients = {}; // connected client dictionary

var next_client_index = 0; // We will give each client a unique id

// for debug, test socket disconnect with '#' key, force disconnect with '='
if ((typeof DEBUG !== 'undefined') && DEBUG.indexOf('rtmonitor_api_log') >= 0)
{
    document.onkeydown = function(evt) {
        evt = evt || window.event;
        log('keydown '+evt.keyCode);
        if (evt.keyCode == 222) // '#' keycode
        {
            test_disconnect();
            //clearInterval(self.progress_timer);
            return;
        }
        if (evt.keyCode == 187) // '=' keycode
        {
            self.disconnect(); // disconnect but do not reconnect
            return;
        }
    }; // end onkeydown
}

// ****************************************************************************
// **************  PUBLIC METHODS      ****************************************
// ****************************************************************************

this.init = function () {
    console.log('RTMonitorAPI', 'WARN - init() called (now redundant)');
};

this.version = function () {
    return VERSION;
}

// ***************************************************************************
// *******************  WebSocket code    ************************************
// ***************************************************************************
// sock_connect() will be called on startup (i.e. in init())
// It will connect socket, when successful will
// send { 'msg_type': 'rt_connect'} message, and should receive { 'msg_type': 'rt_connect_ok' }, then
// send { 'msg_type': 'rt_subscribe', 'request_id' : 'A' } which subsribes to ALL records.
this.connect = function()
{
    log('RTMonitorAPI connect()');

    revive = true; // an unexpected close will try and reconnect

    // Open a new socket if we don't already have a connection
    if (!sock || (sock.readyState == SockJS.CLOSING || sock.readyState == SockJS.CLOSED))
    {
        sock = new SockJS(RTMONITOR_URI);
    }
    else
    {
	    console.log('RTMonitorAPI.connect() re-using existing socket');
    }

    sock.onopen = function() {
                log('** socket open');

                clearInterval(sock_timer); // delete reconnect timer if it's running

                var msg_obj = { msg_type: 'rt_connect',
                                client_data: self.client_data
                              };

                self.sock_send_str(JSON.stringify(msg_obj));
    };

    sock.onmessage = function(e) {
                var msg = JSON.parse(e.data);
                if (msg.msg_type != null && msg.msg_type == "rt_nok")
                {
                    log('RTMonitorAPI error '+e.data);
                    return;
                }
                if (msg.msg_type != null && msg.msg_type == "rt_connect_ok")
                {
                    log('RTMonitorAPI connected OK ('+Object.keys(clients).length+' clients)');

                    rt_connection_status = 'connected';

                    for (var client_id in clients)
                    {
                        if (clients.hasOwnProperty(client_id))
                        {
                            if ( clients[client_id].connected )
                            {
                                clients[client_id].connect_callback();
                            }
                        }
                    }
                    return;
                }

                if (msg.request_id)
                {
                    log('RTMonitorAPI websocket message received for '+msg.request_id);
                    //self.log(e.data);

                    if (!requests[msg.request_id])
                    {
                        log('sock.onmessage','ignoring msg',msg.request_id,'not in requests table');
                        return;
                    }

                    var rq_info = requests[msg.request_id];

                    var client_id = rq_info.client_id;

                    if (!clients[client_id] || !clients[client_id].connected)
                    {
                        log('sock.onmessage','ignoring msg',msg.request_id,'client',client_id,'not connected');
                        return;
                    }

                    rq_info.callback(msg);
                    return;
                }
                else
                {
                    log('RTMonitorAPI websocket message returned with no request_id'+e.data);
                }

    };

    sock.onclose = function() {
                log('sock.onclose','socket closed');

                rt_connection_status = 'disconnected';

                requests = {};

                // check to see if we have any connected clients,
                // if so, call their disconnect_callback().
                // and Warn if "Do Not Resuscitate" is set
                var client_connected = false;

                for (var client_id in clients)
                {
                    if (clients.hasOwnProperty(client_id))
                    {
                        if ( clients[client_id].connected )
                        {
                            client_connected = true;

                            clients[client_id].disconnect_callback();
                        }
                    }
                }

                // if "revive" is true, and we have connected clients, then start reconnect timer
                if (revive && client_connected)
                {
                    console.log('RTMonitorAPI','sock.onclose','starting interval timer trying to reconnect');
                    clearInterval(sock_timer);
                    sock_timer = setInterval(reconnect, 10000);
                } else {
                    if (client_connected)
                    {
                        console.log('RTMonitorAPI',
                                    'sock.close',
                                    'WARN - RTMonitorAPI.disconnect() called with connected clients');
                    }
                }
    }; // end sock.onclose()

}; // end this.connect()

// Disconnect has been explicitly called, so do not resuscitate in 'sock.onclose' callback
this.disconnect = function ()
{
    revive = false; // do not resuscitate
    clearInterval(sock_timer); // stop a prior auto-reconnect timer if it is running
    sock.close();
}

// Register a client to RTMonitorAPI
// will return an object with connect, close, request, subscribe methods
this.register = function (connect_callback, disconnect_callback) {
    var client_id = 'rt_'+(next_client_index++);
    log('this.register','registering client',client_id);
    var client = { client_id:           client_id,
                   connected:           false,
                   connect_callback:    connect_callback,
                   disconnect_callback: disconnect_callback,
                   // Client methods
                   subscribe:           subscribe(client_id),
                   unsubscribe:         unsubscribe(client_id),
                   request:             request(client_id),
                   raw:                 raw(client_id),
                   connect:             client_connect(client_id),
                   close:               client_close(client_id)
                 };
    clients[client_id] = client;
    return client;
}

// Set a new URI for the RTMonitor server.
// This will only take effect on a new 'connect' of rtmonitor_api to the server
this.set_uri = function (new_uri) {
    RTMONITOR_URI = new_uri;
}

// ****************************************************************************
// **************  INTERNAL FUNCTIONS  ****************************************
// ****************************************************************************

// Client has called 'connect' method.
// If RTMonitor is already connected, then call clients 'connect_callback'.
// Otherwise call RTMonitor's connect method to connect RTMonitor to server.
function client_connect(client_id)
{
    return function()
    {
        var client = clients[client_id];
        client.connected = true;
        if (rt_connection_status == 'connected')
        {
            log('client_connect',
                client_id,
                'RTMonitorAPI already connected, so calling connect_callback()');
            client.connect_callback();
        }
        else if (rt_connection_status == 'disconnected')
        {
            log('client_connect',
                client_id,
                'RTMonitorAPI disconnected, so calling RTMonitorAPI.connect()');
            rt_connection_status = 'connecting';
            self.connect();
        }
    }
}

// Client has called 'close' method.
// If that is the last client, RTMonitor will disconnect from server
function client_close(client_id)
{
    return function () { close(client_id); };
}

// Caller has issued a request for one-time return of sensor data
function request(client_id)
{
    return function(request_id, msg_obj, callback)
    {
        var request_id = client_id+'_'+request_id;
        msg_obj.msg_type = 'rt_request';
        msg_obj.request_id = request_id;

        log('request()', request_id);

        var msg = JSON.stringify(msg_obj);

        requests[request_id] = { client_id: client_id,
                                 callback: callback
                               } ;

        return self.sock_send_str(msg);
    };
}

// Return a function that sends a message to the server 'raw', i.e. no mangling the request_id
function raw(client_id)
{
    return function(msg_obj, callback) {
        var request_id = msg_obj.request_id;
        log('raw() ', client_id, request_id);

        if (request_id)
        {
            requests[request_id] = { client_id: client_id,
                                     callback: callback
                                   } ;
        }

        var msg = JSON.stringify(msg_obj);

        return self.sock_send_str(msg);
    };
}

// rt_subscribe is a wrapper that returns a 'subscribe(...)' function with the client_id embedded
function subscribe(client_id)
{
    log('subscribe()','creating subscribe wrapper, client_id',client_id);
    return function(client_request_id, msg_obj, callback) {

                var request_id = client_id+'_'+client_request_id;

                log('subscribe() '+request_id);
                // Note that RTMonitorAPI builds the actual unique request_id that goes to the server
                // as a concatenation of the caller_id and the request_id given by the caller.
                //var caller_request_id = caller_id+'_'+request_id;

                msg_obj.msg_type = 'rt_subscribe';
                //msg_obj.request_id = caller_request_id;
                msg_obj.request_id = request_id;

                log('RTMonitorAPI subscribe request_id '+request_id);

                var msg = JSON.stringify(msg_obj);

                //requests[caller_request_id] = { callback: request_callback } ;
                requests[request_id] = { client_id: client_id,
                                         callback: callback
                                       } ;

                return self.sock_send_str(msg);
               //return subscribe(client_id+'_'+request_id, msg_obj, callback);
    };
}

// rt_unsubscribe is a wrapper that returns an 'unsubscribe(request_id)' function with the client_id embedded
function unsubscribe(client_id)
{
    return function(request_id) {
        log('unsubscribe '+request_id);
        return self.sock_send_str( '{ "msg_type": "rt_unsubscribe", "request_id": "'+client_id+'_'+request_id+'" }' );
    }
}

this.sock_send_str = function(msg)
{
    if (sock == null)
    {
	    log('Socket not yet connected');
	    return { status: 'rt_nok', reason: 'socket not connected' };
    }
    if (sock.readyState == SockJS.CONNECTING)
    {
	    log('Socket connecting...');
	    return { status: 'rt_nok', reason: 'socket still connecting' };
    }
    if (sock.readyState == SockJS.CLOSING)
    {
	    log('Socket closing...');
	    return { status: 'rt_nok', reason: 'socket closing' };
    }
    if (sock.readyState == SockJS.CLOSED)
    {
	    log('Socket closed');
	    return { status: 'rt_nok', reason: 'socket closed' };
    }

    log('RTMonitorAPI sending: '+msg);

    sock.send(msg);

	return { status: 'rt_ok', reason: 'sent message' };
};

function close(client_id)
{
    log('RTMonitorAPI close('+client_id+')');
    if (clients[client_id])
    {
        clients[client_id].connected = false;
        unsubscribe_client(client_id);
    } else
    {
        console.log('RTMonitorAPI','close','client_id',client_id,'not found');
    }
    // iterate through *all* clients and if none are connected to rt_monitor_api then
    // drop the server socket connection
    var client_connected = false; // will set to true if we find *any* client connected
    for (var client_id in clients)
    {
        if (clients.hasOwnProperty(client_id))
        {
            if ( clients[client_id].connected )
            {
                client_connected = true;
                break;
            }
        }
    }
    if (!client_connected)
    {
        log('close()','All clients disconnected, so closing server socket');
        self.disconnect();
    }
}

function unsubscribe_client(client_id)
{
    // client has called 'close(client_id)' method, so
    // iterate through ALL the requests and send 'unsubscribes' for all requests outstanding for this client
    for (var request_id in requests)
    {
        if (requests.hasOwnProperty(request_id))
        {
            if ( requests[request_id].client_id == client_id )
            {
                // NOTE the request_id used in the 'requests' dictionary is the FULL request_id used between
                // this RTMonitorAPI and the server, so we do not mangle it to include the client_id as was
                // done when the request was created.
                log('unsubscribe_client()',client_id,request_id);
                self.sock_send_str( '{ "msg_type": "rt_unsubscribe", "request_id": "'+request_id+'" }' );
            }
        }
    }
}

function test_disconnect()
{
    log('TEST ** closing socket...');
    sock.close();
}

function reconnect()
{
    log('sock_reconnect trying to connect');
    self.connect();
}

function log(str)
{
    if ((typeof DEBUG !== 'undefined') && DEBUG.indexOf('rtmonitor_api_log') >= 0)
    {
        var args = [].slice.call(arguments);
        args.unshift('[RTMonitorAPI]');
        console.log.apply(console, args);
    }
}

// END of 'class' RTMonitorAPI
}
