import simplejson as json

import requests

json_string = """
{"request_data":[
    {   "acp_id": "coffee_pot",
        "acp_units": { "weight": "GRAMS" },
        "acp_sensor_type": "coffee_pot",
        "acp_ts": 1570780665.123,
        "event_type": "fill",
        "weights": [ { "acp_ts": 1570780662.123, "weight": -1.23 },
                     { "acp_ts": 1570780662.523, "weight": 901.235 },
                     { "acp_ts": 1570780662.823, "weight": 2501.235 }
                   ]

    }
    ],
    "module_name":"feedmaker",
    "module_id":"test",
    "feed_id":"general",
    "filename":"1570780665.964_2019-10-11-08-57-45",
    "filepath":"2019/10/11",
    "ts":1570780665,
    "msg_type":"csn_sensor"
}
"""

post_data = json.loads(json_string)

print("module_name", post_data['module_name'])

print("filepath", post_data['filepath'])

#post_data = json.loads('{"foo": 123, "doo": "four-five-six", "goo": "2019/10/11" }')

response = requests.post('https://tfc-app2.cl.cam.ac.uk/test/feedmaker/test/general',
              headers={'X-Auth-Token':'testtoken'},
              json=post_data
              )

print("status code",response.status_code)

