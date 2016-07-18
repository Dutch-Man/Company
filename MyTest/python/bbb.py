#!/usr/bin/python
#coding:utf-8
class Test():
    val1 = 1
    def __init__(self):
        val2 = 2
        self.val3 = 3
    def fun(self):
        Test.val1 += 1 
    ''' 
    def show(self):
        print "m = %d"%m
        print "n = %d"%n
    '''
def main():
    print "Test.val1 = %d"%Test.val1
    test1 = Test()
    test1.fun()
    print "Test.val1 = %d"%Test.val1
    print "test1.val1 = %d"%test1.val1
    print ""

    print id(Test.val1)
    test2 = Test()
    print id(test2.val1)
    test2.fun()
    print id(Test.val1)
    print id(test2.val1)


    print "Test.val1 = %d"%Test.val1
    print "test1.val1 = %d"%test1.val1
    print "test2.val1 = %d"%test2.val1
    print ""


if __name__ == "__main__":
    main()
