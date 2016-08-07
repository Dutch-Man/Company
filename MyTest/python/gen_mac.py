#!/usr/bin/python
#coding:utf-8
import hashlib

def gen_mac_from(strs):
    print strs
    strs_md5 = hashlib.md5(strs).hexdigest()
    print strs_md5
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
    a = "test_ruishi_1"
    b = "test_ruishi_2"
    a_md5 = hashlib.md5(a).hexdigest()
    b_md5 = hashlib.md5(b).hexdigest()
    print a_md5 + "\n" + b_md5
    print gen_mac_from(a)
    #print gen_mac_from(b)


if __name__ == "__main__":
    main()



