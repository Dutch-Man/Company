#!/usr/bin/python
#coding:utf-8
import sys
import time

class A:
    def __init__(self):
	self.a = 10
class B:
    a = A
def main():
    a = {'name':'Bruce','age':'24','job':'IT'}
    print a['name']
if __name__ == "__main__":
    main()
