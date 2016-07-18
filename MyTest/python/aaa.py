#!/usr/bin/python
#coding:utf-8
class Test():
    val1 = 1
    def __init__(self):
        val2 = 2
        self.val3 = 3
    def fun():
        val4 = 4
        self.val5 = 5

def main():
    test = Test()
    print "dir(Test) :",dir(Test)
    print "dir(test) :",dir(test)

if __name__ == "__main__":
    main()
