"use strict";
// ***************************************************************************
// *******************  Page and map code ************************************
// ***************************************************************************
// Constants

var VERSION = '7.02';
            // 7.01 connecting, requesting, subscribing on startup
            // 7.00 rtclient.js -> xcoffee.js
            // 6.01 client/rtmonitor connecting on tfc-app2
            // 6.00 rtclient - removed all bus stuff
            // 5.06 token support, set_uri added to RTMONITOR_API
            // 5.05 bugfix for TIMETABLE_URI
            // 5.04 updated to use rtmonitor_api 3.0 (register & connect methods)
            // 5.03 added transport/stops API to retrieve stops within bounding box
            // 5.02 remove local rt socket code and use RTMonitorAPI from tfc_web
            // 5.01 move bus tracking code into ../rt_tracking, generalize API for tracking
            // 4.10 add rtmonitor-config.js and API key support
            // 4.09 rtmonitor websocket uri now https, added blur callback for change on page
            // 4.08 improving polygon draw support
            // 4.07 forward/back scroll through sock send messages, subscribe link on bus popup
            // 4.06 display/update RTMONITOR_URI on page
            // 4.05 will now get_route() and draw_route_profile() on bus popup -> journey
            // 4.04 geo.js get_box() and is_inside() testing
            // 4.03 using stop -> journeys API
            // 4.02 restructure to use sensor.state.route_profile and not .route
            // 4.01 adding timetable API call to lookup sirivm->route
            // 3.12 added 'pattern_starting' sensor state variable 0..1
            // 3.11 improve timetable vector from prior start stub
            // 3.10 segment_progress (not path_progress)
            // 3.09 progess (still as 'path progress')
            // 3.08 added stop delay to (path) progress
            // 3.06 more work on (path) progress vector
            // 3.04 'before' function added to segment distance
            // 3.03 'beyond' function added to segment distance
            // 3.01 added basic timetable vector (binary started /not started)
            // 2.00 initial development of 'progress vector'
            // 1.00 initial development of 'segment distance vector'

// All supplied from rtroute_config.js
// var RTMONITOR_URI = '';

var DEBUG = '';

// RTMonitor rt_connect client_data
var CLIENT_DATA = { rt_client_name: 'xcoffee V'+VERSION,
                    rt_client_id: 'rtclient',
                    rt_token: '' // will update in init
                  };

// *************************************************************
// *************************************************************
// Globals
// *************************************************************
// *************************************************************
var urlparams = new URLSearchParams(window.location.search);
var debug = urlparams.has('debug');

var OLD_TIMER_INTERVAL = 30; // watchdog timer interval (s) checking for old data records
var OLD_DATA_RECORD = 60; // time (s) threshold where a data record is considered 'old'

var clock_time; // the JS Date 'current time', either now() or replay_time
var clock_timer; // the intervaltimer to update the clock in real time (not during replay)

var log_div; // page div element containing the log

var log_record_odd = true; // binary toggle for alternate log background colors

var log_append = false;

var log_data = false;

var events_div; // Events list dom object

var msg_classname = 'msg_B'; // classname for page message div, will toggle 'msg_A'|'msg_B'

// *********************************************************
// RTRoutes globals

// Sensor data - dictionary of sensors by sensor_id
var sensors = {};
// Where each sensor:
// sensor
//    .msg                - the most recent data message received for this sensor
//    .bus_tracker        - function object containing route tracking state
//    .prev_segment_index - memory of previous segment_index for drawing highlight lines on change
//    .route_highlight    - route highlight drawn line
//    .old                - boolean when sensor data is 'old'


// Message history for socket messages SENT
var rt_send_history =  [];

var rt_history_cursor = 0; // index to allow user scrolling through history

// Data recording
var recorded_records = [];
var recording_on = false;

// Replay
var replay_time; // holds JS Date, current time of replay
var replay_timer; // the JS interval timer for the replay function
var replay_on = false; // Replay mode on|off
var replay_interval = 1; // Replay step interval (seconds)
var replay_speedup = 10; // relative speed of replay time to real time
var replay_index = 0; // current index into replay data
var replay_errors = 0; // simple count of errors during replay
var replay_stop_on_error = false; // stop the replay if annotation doesn't match analysis

// Batch replay
var batch = false;

// Here we define the 'data record format' of the incoming websocket feed
var RECORD_INDEX = 'acp_id';  // data record property that is primary key
var RECORDS_ARRAY = 'request_data'; // incoming socket data property containing data records
var RECORD_TS = 'acp_ts'; // data record property containing timestamp
var RECORD_TS_FORMAT = 'unix'; // data record timestamp format
                                  // 'ISO8601' = iso-format string
var RECORD_LAT = 'Latitude';      // name of property containing latitude
var RECORD_LNG = 'Longitude';     // name of property containing longitude

// *********************************************************************************
var RTMONITOR_API = null;

var rt_mon; // rtmonitor_api client object

var msg_list=["1"];

// ********************************************************************************
// ********************************************************************************
// ***********  XCOFFEE        ****************************************************
// ********************************************************************************
// ********************************************************************************

// POT WEIGHTS
//
var POT_WEIGHT_FULL = 3400;
var POT_WEIGHT_EMPTY = 1630;

// Image elements
var pot_top;
var pot_below;
var pot_empty;
var pot_removed;
var pot_disconnected;

// lower limit of coffee
var POT_BOTTOM_Y = 454;

// Y-pixel of ratio = 1
var POT_MAX_Y = 160;
// Y-pixel of ratio = 0
var POT_MIN_Y = 421;

// PX offset from top of pot_top image to the y-value representing the reading
var POT_TOP_OFFSET = 30;
var POT_BOTTOM_OFFSET = 40;

// chart.js object for brewing progress donut
var brew_progress_chart;
// JS interval timer for brewing progress update
var brew_timer = null;
// Brewing start time            
var brew_start;
// Seconds for full brew
var BREW_TIME = 320;

var pot_is_empty;

function xcoffee_init()
{
    console.log("init()");
    document.title = 'xcoffee V' + VERSION;

    // The 2 images that move up and down to display the coffee level.
    pot_top = document.getElementById("pot_top");
    pot_below = document.getElementById("pot_below");
    pot_empty = document.getElementById("pot_empty");
    pot_removed = document.getElementById("pot_removed");
    pot_disconnected = document.getElementById("pot_disconnected");

    events_div = document.getElementById("events");

    pot_is_empty = false;

    rt_mon = RTMONITOR_API.register(xcoffee_connected, rtmonitor_disconnected);

    rt_mon.connect()

    xcoffee_update_pot(0);
}

// Convert a pot 'fullness' ratio to a Y-pixel value representing the reading
function ratio_to_y(ratio)
{
    return Math.floor(ratio * (POT_MAX_Y - POT_MIN_Y) + POT_MIN_Y)
}

function xcoffee_update_pot(ratio)
{
    var y = ratio_to_y(ratio);

    //console.log("y=",y);

    pot_top.style['top'] = (y - POT_TOP_OFFSET)+"px";
    pot_below.style['top'] = y + "px";
    pot_below.style['height'] = (POT_MIN_Y - y) + POT_BOTTOM_OFFSET + "px";

    if (ratio == 0 && !pot_is_empty)
    {
        console.log("new empty pot");

        pot_empty.style['display'] = "block";
        pot_is_empty = true;
    }
    else if (ratio != 0 && pot_is_empty)
    {
        console.log("new non-empty pot");

        pot_empty.style['display'] = "none";
        pot_is_empty = false;
    }
}

// Draw the initial 'zero' donut on the pot_canvas
function draw_brew_progress(ctx)
{
    // And for a doughnut chart
    var data = {
        datasets: [{
            data: [0, 1], // The donut is two data values, initially shows zero visible.
            backgroundColor: [ 'rgba(255,100,100,0.3)', 'rgba(100,255,100,0.1)']
        }]
    };
    // Here we actually create the chart
    brew_progress_chart = new Chart(ctx, {
        type: 'doughnut',
        data: data,
        options: {
            animation: { duration: 0 }
        }
    });
    
}

function update_brew_progress(ratio) {
    brew_progress_chart.data.datasets[0].data = [ratio, 1-ratio];
    brew_progress_chart.update();
}

function update_brew()
{
    var brew_ratio = ((new Date()).getTime() - brew_start) / (BREW_TIME*1000);
    if (brew_ratio > 1)
    {
        end_brew();
    }
    else
    {
        update_brew_progress(brew_ratio);
        xcoffee_update_pot(brew_ratio);
    }
}

function start_brew()
{
    var ctx = document.getElementById('pot_canvas').getContext('2d');
    brew_start = (new Date()).getTime();
    draw_brew_progress(ctx);
    brew_timer = setInterval(update_brew,1000);
    console.log("Brew animation started");
}

function end_brew()
{
    console.log("Brew animation ended");
    clearInterval(brew_timer);
    brew_timer = null;
    const canvas = document.getElementById('pot_canvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
}

// HERE IS WHERE WE HANDLE THE INCOMING EVENTS FROM THE XCOFFEE SENSOR NODE.
function xcoffee_handle_msg(msg)
{
    console.log('xcoffee msg',msg);

    events_div.insertBefore(xcoffee_format_msg(msg),events_div.firstChild);

    if ( msg["weight"] != null )
    {
        var ratio = (msg["weight"] - POT_WEIGHT_EMPTY) / (POT_WEIGHT_FULL - POT_WEIGHT_EMPTY)

        if (ratio > 1)
        {
            ratio = 1;
        }
        else if (ratio < 0.04)
        {
            ratio = 0;
        }

        xcoffee_update_pot(ratio);

        var display_weight = ratio == 0 ? 'EMPTY' : Math.floor(msg["weight"] - POT_WEIGHT_EMPTY);

        var display_color = ratio == 0 ? "red" : "green";

        // display the weight text as cylinder overlay on pot graphic.
        draw_cyl_text('pot_canvas',
                 display_weight,40, 95, "green" , // text, height px, offset_x, color
                 148,375,196,35 // cylinder offset_x, offset_y, width, angle
                 );
    }


    // For previous "COFFEE_NEW", add cylinder text overlay for "new brew time" to pot graphic.
    if ( msg["new_status"] != null )
    {
        let unix_timestamp = msg["new_status"]["acp_ts"]
        // Create a new JavaScript Date object based on the timestamp
        // multiplied by 1000 so that the argument is in milliseconds, not seconds.
        var date = new Date(unix_timestamp * 1000);
        // Hours part from the timestamp
        var hh = ("0"+date.getHours()).substr(-2);
        // Minutes part from the timestamp
        var mm = ("0" + date.getMinutes()).substr(-2);

        draw_cyl_text('pot_canvas',
                 hh+':'+mm,60,60,"red",
                 148,155,196,25);
    }

    console.log("msg event_code =",msg["event_code"])
    if ( msg["event_code"] == "COFFEE_REMOVED" )
    {
        pot_removed.style['display'] = 'block';
    }
    else if (msg["event_code"] != null)
    {
        console.log('display=none for pot_removed')
        pot_removed.style['display'] = 'none';
    }
}

//subscribe to events from RT_SENSOR_ID
function xcoffee_subscribe(sensor_id)
{
    console.log('** subscribing to',sensor_id);

    var msg_obj = { msg_type: 'rt_subscribe',
                    request_id: 'A',
                    filters: [ { test: "=",
                                 key: "acp_id",
                                 value: sensor_id } ]
                  };
    //sock_send_str(JSON.stringify(msg_obj));
    rt_mon.subscribe(sensor_id, msg_obj, handle_records);
}

//subscribe to events from RT_SENSOR_ID (set in index.html)
function xcoffee_request(sensor_id)
{
    console.log('** requesting latest message from',sensor_id);

    var msg_obj = { options: ['latest_records'],
                    filters: [ { test: "=",
                                 key: "acp_id",
                                 value: sensor_id } ]
                  };
    //sock_send_str(JSON.stringify(msg_obj));
    rt_mon.request('B', msg_obj, handle_records);
}

function xcoffee_connected()
{
    console.log('** xcoffee connected **');
    pot_disconnected.style['display'] = 'none';
    document.getElementById('connect_box').className = 'connected';

    rtmonitor_connected();

    xcoffee_request(RT_SENSOR_ID);

    xcoffee_subscribe(RT_SENSOR_ID);
}

function xcoffee_disconnected()
{
    rtmonitor_disconnected();
}

// Format the incoming message for display on the page
function xcoffee_format_msg(msg)
{
    var div = document.createElement('div');
    // toggle classname between msg_A and msg_B
    msg_classname = msg_classname == 'msg_A' ? 'msg_B' : 'msg_A';

    div.className = msg_classname;

    var div_content = document.createTextNode(JSON.stringify(msg));
    div.appendChild(div_content);
    return div;
}

// draw_cyl_text() will draw a text string on a canvas as if it is wrapped around a cylinder.
// The basic technique is to draw the text on an internal 'working' canvas (called 'image'), and then copy
// vertical slices of that image to the DOM canvas with a suitable x shift (for cylinder effect) and
// y shift (for tilt).
function draw_cyl_text(
                canvas_id, // id of DOM canvas element on which to draw the text
                text,      // Text string to draw
                text_h, text_offset_x, // px values for text height and offset from left side of cylinder
                text_color, // color for text foreground (background is transparent)
                // cylinder parameters (in px):
                cyl_offset_x, // cylinder offset from left edge of canvas
                cyl_offset_y, // cylinder offset from top of canvas
                cyl_width,    // diameter of cylinder (i.e. width as seen on canvas)
                cyl_angle_px) // pixel downshift of center of text, creating apparent tilt.
{
    console.log("draw_cyl_text",text);

    // destination DOM canvas to receive the distorted text image
    var drawing_canvas = document.getElementById(canvas_id);
    var dctx = drawing_canvas.getContext("2d");
    var dw = drawing_canvas.width // DRAWING width of cylinder

    dctx.clearRect(0, cyl_offset_y, dw, text_h + cyl_angle_px)

    // 'working' canvas to contain the undistorted text 'image'
    // Image width (iw) and height (ih).
    // Because the wrapped image covers the facing half of the cylinder, we can
    // calculate the necessary width of the image as (pi/2)*(the cylinder width)
    var iw = cyl_width * Math.PI / 2.0;
    // The image height is simply however tall the text is.
    var ih = text_h;

    var image = document.createElement("canvas");
    image.width = iw;
    image.height = ih;
    var ictx = image.getContext("2d");
    ictx.font = text_h*1.3+"px arial";
    ictx.textAlign = "left";
    //ictx.fillStyle = "#7F5";
    //ictx.fillRect(0,0,iw,ih)
    ictx.fillStyle = text_color;
    ictx.fillText(text,text_offset_x,text_h)

    // iterate through each 1-pixel column of the image
    for (var ix=0; ix<iw; ix++)
    {
        // destination x offset
        var dx = cyl_offset_x - iw / Math.PI * Math.cos(ix / iw * Math.PI);
        // destination y offset
        var dy = cyl_offset_y + cyl_angle_px * Math.sin(ix / iw * Math.PI);
        // destination height (in case we add perspective)
        var dh = ih;
        //
        dctx.drawImage(image, // source image
                    ix,    // source x
                    0,     // source y
                    1,     // source width
                    ih,    // source height
                    dx,    // destination x
                    dy, // y- s * perspective*0.5, // destination y
                    1,     // destination width
                    dh // 200 + s * perspective // destination height
                    );
    }
}


// *********************************************************************************
// *********************************************************************************
// ********************  INIT RUN ON PAGE LOAD  ************************************
// *********************************************************************************
// *********************************************************************************
function init()
{
    //initialise page_title
    var page_title_text = document.createTextNode('xcoffee V'+VERSION);
    var page_title = document.getElementById('page_title');
    // remove existing title if there is one
    while (page_title.firstChild) {
            page_title.removeChild(page_title.firstChild);
    }

    document.getElementById('page_title').appendChild(page_title_text);

    if (/[?&]dev=true/.test(location.search))
    {
        // Choose whether to display the control div
        var events_div = document.getElementById('events');
        var control_div = document.getElementById('control_div');
        control_div.style.display = "inline-block";
        events_div.style.display = "block";
    }

    // initialize log 'console'
    log_div = document.getElementById('log_div');

    // display RTMONITOR_URI on control div
    var rtmonitor_uri_input = document.getElementById('rtmonitor_uri');

    rtmonitor_uri_input.value = RTMONITOR_URI;

    CLIENT_DATA.rt_token = RT_TOKEN; // from rtclient.html

    rtmonitor_uri_input.addEventListener('focus', function (e) {
        rtmonitor_uri_input.style['background-color'] = '#ddffdd'; //lightgreen
        return false;
    });

    rtmonitor_uri_input.addEventListener('blur', function (e) {
        RTMONITOR_URI = rtmonitor_uri_input.value;
        RTMONITOR_API.set_uri(RTMONITOR_URI);
        console.log('RTMONITOR_URI changed to '+RTMONITOR_URI);
        rtmonitor_uri_input.style['background-color'] = '#ffffff'; //white
        return false;
    });

    rtmonitor_uri_input.addEventListener('keydown', function (e) {
        if (e.key === "Enter" || e.keyCode == 13 || e.which == 13)
        {
            RTMONITOR_URI = rtmonitor_uri_input.value;
            RTMONITOR_API.set_uri(RTMONITOR_URI);
            console.log('RTMONITOR_URI changed to '+RTMONITOR_URI);
            rtmonitor_uri_input.blur();
            e.preventDefault();
            return false;
        }
        return false;
    });

    update_clock(new Date());

    clock_timer = setInterval(function () { update_clock(new Date()); }, 1000);

    // initialize UI checkboxes

   // document.getElementById('log_append').checked = false;

    // watchdog timer checking for 'old' data records

    setInterval(check_old_records, OLD_TIMER_INTERVAL*1000);

    RTMONITOR_API = new RTMonitorAPI(CLIENT_DATA, RTMONITOR_URI);

    xcoffee_init();
    //rt_mon.connect();

} // end init()

// ********************************************************************************
// ********************************************************************************
// ***********  Process the data records arrived from WebSocket or Replay *********
// ********************************************************************************
// ********************************************************************************

// Process websocket data
function handle_records(websock_data)
{
    //console.log(websock_data);
    //var incoming_data = JSON.parse(websock_data);
    //console.log('handle_records'+json['request_data'].length);
    for (var i = 0; i < websock_data[RECORDS_ARRAY].length; i++)
    {
	    handle_msg(websock_data[RECORDS_ARRAY][i], new Date());
    }
} // end function handle_records

// process a single data record
function handle_msg(msg, clock_time)
{
    // add to recorded_data if recording is on

    if (recording_on)
    {
        recorded_records.push(JSON.stringify(msg));
    }

    var sensor_id = msg[RECORD_INDEX];

    console.log("Got message: "+JSON.stringify(msg));

    // If an existing entry in 'sensors' has this key, then update
    // otherwise create new entry.
    if (sensors.hasOwnProperty(sensor_id))
    {
        update_sensor(msg, clock_time);
    }
    else
    {
        init_sensor(msg, clock_time);
    }

}

// We have received data from a previously unseen sensor, so initialize
function init_sensor(msg, clock_time)
    {
        // new sensor, create marker
        console.log(" ** New sensor id:'"+msg[RECORD_INDEX]+"'");

        var sensor_id = msg[RECORD_INDEX];

        var sensor = { sensor_id: sensor_id,
                       msg: msg
                     };

      // flag if this record is OLD or NEW
        init_old_status(sensor, clock_time);

        sensors[sensor_id] = sensor;

        xcoffee_handle_msg(msg);
    }

// We have received a new data message from an existing sensor, so analyze and update state
function update_sensor(msg, clock_time)
{
		// existing sensor data record has arrived
        //console.log('update_sensor '+clock_time);

        var sensor_id = msg[RECORD_INDEX];

		if (get_msg_date(msg).getTime() != get_msg_date(sensors[sensor_id].msg).getTime())
        {

            // store as latest msg
            // moving current msg to prev_msg
            sensors[sensor_id].prev_msg = sensors[sensor_id].msg;
		    sensors[sensor_id].msg = msg; // update entry for this msg

            var sensor = sensors[sensor_id];

            console.log('Updating '+sensor.sensor_id);

            // flag if this record is OLD or NEW
            update_old_status(sensor, clock_time);

            xcoffee_handle_msg(msg);
		}
}

// update realtime clock on page
// called via intervalTimer in init()
function update_clock(time)
{
    clock_time = time;
    document.getElementById('clock').innerHTML = hh_mm_ss(time);
    check_old_records(time);
}

// Given a data record, update '.old' property t|f and reset marker icon
// Note that 'current time' is the JS date value in global 'clock_time'
// so that this function works equally well during replay of old data.
//
function init_old_status(sensor, clock_time)
{
    sensor.old = false; // start with the assumption msg is not old, update will correct if needed
    update_old_status(sensor, clock_time);
}

function update_old_status(sensor, clock_time)
{
    var data_timestamp = get_msg_date(sensor.msg); // will hold Date from sensor

    // calculate age of sensor (in seconds)
    var age = (clock_time - data_timestamp) / 1000;

    if (age > OLD_DATA_RECORD)
    {
        // data record is OLD
        // skip if this data record is already flagged as old
        if (sensor.old != null && sensor.old)
        {
            return;
        }
        // set the 'old' flag on this record and update icon
        sensor.old = true;
        console.log("Sensor "+sensor.sensor_id+" is now old")
    }
    else
    {
        //console.log('update_old_status NOT OLD '+sensor.sensor_id);
        //var clock_time_str = hh_mm_ss(clock_time);
        //var msg_time_str = hh_mm_ss(data_timestamp);
        //console.log(clock_time_str+' vs '+msg_time_str+' data record is NOT OLD '+sensor.sensor_id);

        // skip if this data record is already NOT OLD
        if (sensor.old != null && !sensor.old)
        {
            return;
        }
        // reset the 'old' flag on this data record and update icon
        sensor.old = false;
        console.log("Sensor "+sensor.sensor_id+" not old any more")

    }
}

// watchdog function to flag 'old' data records
// records are stored in 'sensors' object
function check_old_records(clock_time)
{
    //console.log('checking for old data records..,');

    var check_time = new Date();
    if (clock_time != null)
    {
        check_time = clock_time;
    }

    // do nothing if timestamp format not recognised
    switch (RECORD_TS_FORMAT)
    {
        case 'ISO8601':
            break;

        default:
            return;
    }

    for (var sensor_id in sensors)
    {
        //console.log('check_old_records '+sensor_id);
        update_old_status(sensors[sensor_id], check_time);
    }
}

// return provided JS Date() as HH:MM:SS
function hh_mm_ss(datetime)
{
    var hh = ('0'+datetime.getHours()).slice(-2);
    var mm = ('0'+datetime.getMinutes()).slice(-2);
    var ss = ('0'+datetime.getSeconds()).slice(-2);
    return hh+':'+mm+':'+ss;
}


// return a JS Date() from bus message
function get_msg_date(msg)
{
    switch (RECORD_TS_FORMAT)
    {
        case 'ISO8601':
            return new Date(msg[RECORD_TS]);
            break;

        case 'unix':
            return new Date(msg[RECORD_TS]*1000);
            break;

        default:
            break;
    }
    return null;
}

// ***************************************************************************
// *******************  RTmonitor calls/callbacks ****************************
// ***************************************************************************

// user has clicked the 'connect' button
function rt_connect()
{
    console.log('** connecting rtmonitor **');
    rt_mon.connect();
}

// user has clicked the 'close' button
function rt_disconnect()
{
    console.log('** disconnecting rtmonitor **');
    pot_disconnected.style['display'] = 'block';
    document.getElementById('connect_box').className = 'not_connected';
    rt_mon.close();
}

function rtmonitor_disconnected()
{
    console.log('** rtmonitor connection closed **');
    pot_disconnected.style['display'] = 'block';
    document.getElementById('connect_box').className = 'not_connected';
}

function rtmonitor_connected()
{
    console.log('** rtmonitor connected **');
    pot_disconnected.style['display'] = 'none';
    document.getElementById('connect_box').className = 'connected';
}

function rt_send_input(input_name)
{
    var str_msg = document.getElementById(input_name).value;

    rt_send_raw(str_msg);
}

function rt_send_raw(str_msg)
{
    console.log('sending: '+str_msg);

    // push msg onto history and update cursor to point to end
    rt_send_history.push(str_msg);

    rt_history_cursor = rt_send_history.length;

    // write msg into scratchpad textarea
    document.getElementById('rt_scratchpad').value = str_msg;

    rt_mon.raw(JSON.parse(str_msg), handle_records);
}

// switch the console log between newest msg on top vs newest on bottom
function click_log_append()
{
    var prev_log_append = log_append;
    log_append = document.getElementById("log_append").checked == true;
    if (prev_log_append != log_append)
    {
        log_reverse();
    }
}

function click_log_data()
{
    log_data = document.getElementById("log_data").checked == true;
}

// empty textarea e.g. scratchpad
function clear_textarea(element_id)
{
    document.getElementById(element_id).value='';
}

// scroll BACK through socket messages sent to server and update scratchpad
function rt_prev_msg(element_id)
{
    // don't try and scroll backwards before start
    if (rt_history_cursor <= 1)
    {
        return;
    }

    rt_history_cursor--;

    document.getElementById(element_id).value = rt_send_history[rt_history_cursor-1];
}

// scroll FORWARDS through socket messages sent to server
function rt_next_msg(element_id)
{
    // don't scroll forwards after last msg
    if (rt_history_cursor >= rt_send_history.length)
    {
        return;
    }

    rt_history_cursor++;

    document.getElementById(element_id).value = rt_send_history[rt_history_cursor-1];
}

// issue a request to server for the latest records
function request_latest_records()
{
    //sock_send_str('{ "msg_type": "rt_request", "request_id": "A", "options": [ "latest_records" ] }');
    var msg = {  options: [ 'latest_records' ] };
    rt_mon.request('A',msg,handle_records);
}

// issue a subscription to server for all records
function subscribe_all()
{
    rt_mon.subscribe('A',{},handle_records);
    //sock_send_str('{ "msg_type": "rt_subscribe", "request_id": "A" }');
}

//user clicked on 'subscribe' for a bus
function subscribe_to_sensor(sensor_id)
{
    var msg_obj = { msg_type: 'rt_subscribe',
                    request_id: sensor_id,
                    filters: [ { test: "=", key: "VehicleRef", value: sensor_id } ]
                  };
    //sock_send_str(JSON.stringify(msg_obj));
    rt_mon.subscribe(sensor_id, msg_obj, handle_records);
}

// user has clicked the 'Reset' button
function page_reset()
{
    init();
}



// *************************************************************
// Recording buttons
// *************************************************************

function record_start()
{
    recording_on = true;
    document.getElementById('record_start').value = 'Recording';
}

function record_clear()
{
    recording_on = false;
    recorded_records = [];
    document.getElementById('record_start').value = 'Record';
}

function record_print()
{
    console.log('Printing '+recorded_records.length+' recorded records to console');
    var msgs = '[\n';
    for (var i=0; i<recorded_records.length; i++)
    {
        msgs += JSON.stringify(recorded_records[i]);
        if (i < recorded_records.length-1)
        {
            msgs += ',\n';
        }
        else
        {
            msgs += '\n]';
        }
    }
    console.log(msgs);
}

