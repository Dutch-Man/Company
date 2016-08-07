#include <iostream>
#include "opencv2/opencv.hpp"
#include <stdio.h>
using namespace std;
using namespace cv;
int main()
{
	Mat test(320, 320, CV_8UC3, Scalar(180, 120, 50));
	Mat test_back(400, 400, CV_8UC3, Scalar(0,0,0));
	Point cent(test.rows / 2, test.cols / 2);
	circle(test, cent, 10, Scalar(255, 0, 0), 100);	
	//circle(test, cent, 2, Scalar(0, 255, 0), 5); //Draw inner circle
	
	Mat mask(320, 320, CV_8UC3, Scalar(0, 0, 0));
	test.empty();
	test.copyTo(test_back(Rect(10, 20, 320, 320)));
	
	printf("x = %d\n",cent.x);

	//»­»úÆ÷ÈË
	int rows, cols;
	rows = 100; 
	cols = 100;
	Mat roobt_mat(rows, cols, CV_8UC3, CV_RGB(100, 100, 100));
	roobt_mat.setTo(255);
	Mat robot = imread("robot.jpg");
	if (!robot.data)
	{
		cout << "Í¼Ïñ¼ÓÔØÊ§°Ü!\n";
		return 0;
	}
	imshow("test", robot);
	cout<<robot.rows<<endl<<robot.cols<<endl;
	cout<<robot.size().width<<endl<<robot.size().height<<endl;
	Mat robot_flip;
	flip(robot,robot_flip,0);
	imshow("flip",robot_flip);
	waitKey(0);
	return 0;
}
