#!/bin/bash

cat $1 | jq '.request_data[0] | [ .acp_ts, .weight ] | @csv' | sort 
