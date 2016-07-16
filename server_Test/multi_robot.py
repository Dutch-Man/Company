#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# @author renjp115910@hanslaser.com
# @date 2016-06-28
#

import os
import time
def main():
#	cmd = "./robot_faker.py 120.76.189.9:5010 -r register --sn xxxx-yyyy-zzzz-" #设备注册
	cmd = "./robot_faker.py 120.76.189.9:5010 --sn xxxx-yyyy-zzzz-" #设备上线
	for i in range(1,11):
		s = "%d"%(i)
		cmd_s = cmd + s + " > log/sn-" + s + ".log" + " &"
#		cmd_s = cmd + s + " &"
		os.system(cmd_s)
		time.sleep(0.2)

if __name__ == '__main__':
	main()
