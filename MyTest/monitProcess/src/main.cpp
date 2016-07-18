#include <stdio.h>
#include <vector>
using namespace std;
int main()
{
	int n = 0;
	printf("Test is running ......\n");
	vector<int> vec;
	while(1)
	{
		printf("%d\n",n++);
		vec.push_back(n);
	}
	return 0;
}
