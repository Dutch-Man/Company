#!/usr/bin/python
#coding:utf-8
import urllib, json
import sys
 
def sendsms(appkey, mobile, tpl_id, tpl_value):
    sendurl = 'http://v.juhe.cn/sms/send'           # 短信发送的URL,无需修改 
 
    params = 'key=%s&mobile=%s&tpl_id=%s&tpl_value=%s' % \
             (appkey, mobile, tpl_id, urllib.quote(tpl_value)) #组合参数
 
    wp = urllib.urlopen(sendurl+"?"+params)
    content = wp.read()     #获取接口返回内容
 
    result = json.loads(content)
 
    if result:
        error_code = result['error_code']
        if error_code == 0:
            #发送成功
            smsid = result['result']['sid']
            print "sendsms success, smsid: %s" % (smsid)
        else: 
            #发送失败
            print "sendsms error:(%s) %s" % (error_code, result['reason'])
    else:
        #请求失败
        print "request sendsms error"
 
def main():
    if (len(sys.argv) != 2):
        print "Usage: %s CODE" % sys.argv[0]
        return

    code = sys.argv[1]
    appkey = '54c0098217b3d609a965f08bde50bc58'     # 您申请的短信服务appkey
    mobile = '13715171313'                         # 短信接受者的手机号码
    tpl_id = '15668'                                 # 申请的短信模板ID,根据实际情况修改 
    tpl_value = '%23code%23%3D' + code              # 短信模板变量,根据实际情况修改
     
    sendsms(appkey, mobile, tpl_id, tpl_value)      # 请求发送短信
 
if __name__ == '__main__':
    main()
