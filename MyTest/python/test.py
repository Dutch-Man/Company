#!/usr/bin/python
#coding:utf-8
import sys
import time

class A:
    def __init__(self):
    	self.a = 10
    def showself(self):
	print self
class B:
    a = A
def main():
    a = {'name':'Bruce','age':'24','job':'IT'}
    print a['name']
    print A
    a=A()
    a.showself()
    A.showself() 
if __name__ == "__main__":
    main()
