#!/bin/sh
VBoxManage --nologo guestcontrol Lubu_FL_4 run --exe "/usr/bin/python3" --username "lubu" --password "1" --wait-stdout -- python3/arg0 "/home/lubu/Desktop/MQTT_test/test1.py"


