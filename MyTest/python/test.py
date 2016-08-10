#!/usr/bin/python
#coding:utf-8
import sys
import time
import datetime
num = 1

def show():
    global num
    num += 1
    print num

def main():
    print "a",ord("a")
    print "f",ord("f")
    print "z",ord("z")
    #or i in range(102,123)
	#rint (i-) 
    print time.time()
    t1 = datetime.datetime.now()
    time.sleep(0.01)
    t2 = datetime.datetime.now()
    print t1
    print t2
    print type(t1)
    print type(t2-t1)
    print "%s"%(str(t2-t1))
    dic = {1:"1",2:"2"}
    print dic
    del dic[1]
    print dic
if __name__ == "__main__":
    main()
