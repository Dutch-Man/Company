/*
#include "CTest.h"
int main()
{
    CTest test;
    test.show();
    return 0;
}
*/
#include <iostream>
#include <sys/time.h>
#include <stdio.h>
#include <unistd.h>
#include <stdint.h>  
#include <time.h>
#include <sys/time.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sstream>
using namespace std;
int main_1 (void)
{
    int a = 1;
    float b = 0.1;
    double c = 0.02;
    char d[20] = "abcdefg";
    stringstream ss;
    ss<<"{"
      <<"int:"<<a<<","
      <<"float:"<<b<<","
      <<"double:"<<c<<","
      <<"char:"<<d
      <<"}";
    cout<<ss.str()<<endl;
    cout<<time(NULL)<<endl;
    
#define A a
    cout<<a<<endl;
    cout<<A<<endl;
#undef A

}
