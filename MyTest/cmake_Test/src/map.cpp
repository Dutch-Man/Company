#include <iostream>
#include <stdlib.h>
#include <map>
#include <string>
using namespace std;
/*
int main()

{
    map<int, string> mapStudent;
    mapStudent.insert(pair<int, string>(1, “student_one”));
    mapStudent.insert(pair<int, string>(2, “student_two”));
    mapStudent.insert(pair<int, string>(3, “student_three”));
    map<int, string>::iterator  iter;
    for(iter = mapStudent.begin(); iter != mapStudent.end(); iter++)
    {
	cout<<iter->first<<endl<<iter->second<<end;
    }

}
*/
int main_m()
{
    map<int,string> mapStudent;
    mapStudent.insert(pair<int,string>(2,"Lucy"));
    mapStudent.insert(map<int,string>::value_type (1,"Jim"));
    mapStudent[3] =  "Lily";
    cout<<"size = "<<mapStudent.size()<<endl;
    map<int,string>::iterator iter;
    for(iter = mapStudent.begin();iter != mapStudent.end();iter++)
    {
	cout<<"NO. "<<iter->first <<"     name " <<iter->second <<endl;
    }
    cout<<endl;
    for (int i = 0;i<10;i++)
    {
    iter = mapStudent.find(i);
    if (iter != mapStudent.end())
	cout<<iter->first<<" "<<iter->second<<endl;
    else
	cout<<"没找到!\n";
    }
}	
