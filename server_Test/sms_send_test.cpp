#include <stdio.h>
#include <string.h>
#include <curl/curl.h>
#include <json/json.h>

//const char* api_addr = "http://v.juhe.cn/sms/send";
//const char* appkey = "526a1760e4ae1b723e3991fd73675cbe";
//const char* tpl_id = "7765";
//const char* tpl_value = "%23code%23%3D";
const char* api_tpl = "http://v.juhe.cn/sms/send?key=54c0098217b3d609a965f08bde50bc58&tpl_id=15668&tpl_value=%23code%23%3D";

using std::string;
typedef std::string  ResponseData;
char g_errstr[128];
int g_retcode;
 
size_t ReceiveResponseCallback(void *contents, size_t size, size_t nmemb, void *userp)
{
    size_t realsize = size * nmemb;
    ResponseData* rsp_data = (ResponseData *)userp;
    rsp_data->append((char*)contents, realsize);

    return realsize;
}

bool DecodeResponse(const char* rsp_data)
{
    Json::Reader json;
    try
    {
        Json::Value jsondoc;
        if (!json.parse(rsp_data, jsondoc, false))
        {
            g_retcode = -1;
            strncpy(g_errstr, json.getFormattedErrorMessages().c_str(), sizeof(g_errstr));
        }
        else
        {
            g_retcode = atol(jsondoc["error_code"].asString().c_str());
            strncpy(g_errstr, jsondoc["reason"].asCString(), sizeof(g_errstr));
        }
    }
    catch (Json::Exception& e)
    {
        g_retcode = -2;
        strncpy(g_errstr, e.what(), sizeof(g_errstr));
    }

    return json.good() && g_retcode == 0;
}

bool SendAuthCodeBySMS(const char* mobile, const char* authcode)
{
    CURL *curl = NULL;
    CURLcode res;
    ResponseData rsp_data;
    bool decode_success = false;

    curl = curl_easy_init();
    if (curl) {
        string url(1024, '\0');
        url.assign(api_tpl);
        url.append(authcode);
        url.append("&mobile=");
        url.append(mobile);
        printf("url: %s\n", url.c_str());

        curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, ReceiveResponseCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &rsp_data);

        res = curl_easy_perform(curl);
        if (res != 0) {
            printf("Failed: code: %d\n", res);
        } else {
            printf("Success: %lu bytes retrieved, response: %s\n", rsp_data.size(), rsp_data.c_str());
            decode_success = DecodeResponse(rsp_data.c_str());
            printf("Decode response: code: %d, errstr: %s\n", g_retcode, g_errstr);
        }
    }
    curl_easy_cleanup(curl);
    return res == 0 && decode_success;
}

const char* g_json_test = "{\"reason\":\"操作成功\",\"result\":{\"sid\":\"1000616104657085000\",\"fee\":1,\"count\":1},\"error_code\":1}";

int main(void)
{
    curl_global_init(CURL_GLOBAL_ALL);

    SendAuthCodeBySMS("13715171313", "123456");

    curl_global_cleanup();
    /*
    bool decode_success = DecodeResponse(g_json_test);
    printf("Decode response: code: %d, errstr: %s\n", g_retcode, g_errstr);
    */

    return 0;
}

//  g++ -g -o sms_send_test sms_send_test.cpp -lcurl
//  g++ -g --std=c++11 -o sms_send_test sms_send_test.cpp -lcurl -I ../../third_libs/jsoncpp/include/ ../../third_libs/jsoncpp/libs/libjsoncpp.a
