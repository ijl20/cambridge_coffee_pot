#!/bin/bash

curl -X POST -m 15 --header "X-Auth-Token: testtoken" -d @test_eb.json https://tfc-app2.cl.cam.ac.uk/test/feedmaker/test/general
