    // Get the hostname
    if (gethostname(hostname, sizeof(hostname)) != 0) {
        perror("Failed to get hostname");
        return 1;
    }

    // Initialize NVML
    result = nvmlInit();
    if (NVML_SUCCESS != result) {
        printf("Failed to initialize NVML: %s\n", nvmlErrorString(result));
        return 1;
    }

#include <stdio.h>
#include <nvml.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>

#define NUM_ENTRIES_PER_SECOND 100
#define DURATION_SECONDS 300  // 5 minutes

// Function to get the current time in nanoseconds
long long current_time_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

int main() {
    nvmlReturn_t result;
    unsigned int device_count;
    char hostname[256];

    // Get the hostname
    if (gethostname(hostname, sizeof(hostname)) != 0) {
        perror("Failed to get hostname");
        return 1;
    }

    // Initialize NVML
    result = nvmlInit();
    if (NVML_SUCCESS != result) {
        printf("Failed to initialize NVML: %s\n", nvmlErrorString(result));
        return 1;
    }

    // Get the number of GPUs
    result = nvmlDeviceGetCount(&device_count);
    if (NVML_SUCCESS != result) {
        printf("Failed to get device count: %s\n", nvmlErrorString(result));
        nvmlShutdown();
        return 1;
                                                                                                                                             1,1           Top