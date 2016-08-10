#!/usr/bin/python
#coding:utf-8
import hashlib
import random

def gen_mac_from(strs):
    strs_md5 = hashlib.md5(strs).hexdigest()
    mac_str = "%s:%s:%s:%s:%s:%s"%(
		strs_md5[0:2],
		strs_md5[2:4],
		strs_md5[4:6],
		strs_md5[6:8],
		strs_md5[8:10],
		strs_md5[10:12]
		)
    return mac_str

def main():
    for i in range(20):
	strs = "test_ruishi_%d"%i
	#print strs
	print gen_mac_from(strs)


if __name__ == "__main__":
    main()



