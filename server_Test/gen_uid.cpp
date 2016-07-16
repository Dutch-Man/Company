#include <stdio.h>
#include <stdint.h>
#include <time.h>

uint64_t gen_uid(uint64_t mac)
{
    static uint8_t seq = 1;
    uint64_t uid = mac;
    printf("uid: %lx\n", uid);
    uid = uid << 32;
    printf("uid: %lx\n", uid);
    uint32_t now = time(NULL);
    printf("now: %lx\n", now);
    uid = uid | uint64_t(now << 8);
    printf("uid: %lx\n", uid);
    uid = uid | uint64_t(seq++);
    return uid;
}

uint64_t mac_str2num(const char* mac)
{
    uint32_t mac_num[6] = {0};
    sscanf(mac, "%x:%x:%x:%x:%x:%x", &mac_num[5], &mac_num[4], &mac_num[3], &mac_num[2], &mac_num[1], &mac_num[0]);
    //sscanf(mac, "%x:%x:%x:%x:%x:%x", &mac_num[0], &mac_num[1], &mac_num[2], &mac_num[3], &mac_num[4], &mac_num[5]);
    printf("%02x:%02x:%02x:%02x:%02x:%02x\n", mac_num[0], mac_num[1], mac_num[2], mac_num[3], mac_num[4], mac_num[5]);
    uint8_t mac_num_2[6] = {0};
    for (int i = 0; i < 6; i++)
    {
        mac_num_2[i] = (uint8_t)mac_num[i];
    }
    printf("%02x:%02x:%02x:%02x:%02x:%02x\n", mac_num_2[0], mac_num_2[1], mac_num_2[2], mac_num_2[3], mac_num_2[4], mac_num_2[5]);
    return *(uint64_t*)mac_num_2;
}

uint64_t gen_uid(const char* mac)
{
    uint64_t mac_num = mac_str2num(mac);
    printf("mac: %lx\n", mac_num);
    return gen_uid(mac_num);
}

int main(int argc, char* argv[])
{
    if (argc != 2)
    {
        printf("Usage: %s <MAC ADDRESS>\n", argv[0]);
        return 1;
    }

    uint64_t uid = gen_uid(argv[1]);
    printf("uid: %lx\n", uid);

    printf("----------------\n");

    uid = gen_uid(argv[1]);
    printf("uid: %lx\n", uid);

    return 0;
}
