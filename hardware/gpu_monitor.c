#include <stdio.h>
#include <nvml.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/stat.h>

#define SAMPLE_INTERVAL_MS 10    // Sample data every 10 milliseconds
#define SAMPLES_PER_SECOND (1000 / SAMPLE_INTERVAL_MS)  // Samples per second
#define MAX_SAMPLES (SAMPLES_PER_SECOND * 3600)  // Maximum samples for 1 hour
#define CHECK_FILE_INTERVAL 100  // Check file every 100 samples

// Structure for each metric record
typedef struct {
    unsigned int temp;
    unsigned int clock;
    float power;
    long long timestamp;
} MetricRecord;

// Thread arguments structure
typedef struct {
    unsigned int gpu_index;
    nvmlDevice_t device;
    char hostname[256];
    MetricRecord* buffer;    // Pointer to this GPU's data buffer
    int samples_collected;   // Number of samples actually collected
} ThreadArgs;

// Function to get the current time in nanoseconds
long long current_time_ns() {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

// More precise sleep function
void precise_sleep(long long target_time) {
    struct timespec ts;
    long long current = current_time_ns();
    if (target_time > current) {
        ts.tv_sec = (target_time - current) / 1000000000LL;
        ts.tv_nsec = (target_time - current) % 1000000000LL;
        nanosleep(&ts, NULL);
    }
}

// Check if file exists
int file_exists(const char* filename) {
    struct stat buffer;
    return (stat(filename, &buffer) == 0);
}

// GPU monitoring thread function
void* monitor_gpu(void* arg) {
    ThreadArgs* args = (ThreadArgs*)arg;
    nvmlReturn_t result;
    args->samples_collected = 0;
    int check_counter = 0;
    
    long long start_time = current_time_ns();
    long long next_sample_time = start_time;
    
    // Collect samples until task1_completed file is found
    while (args->samples_collected < MAX_SAMPLES) {
        // Check for completion file periodically
        if (++check_counter >= CHECK_FILE_INTERVAL) {
            if (file_exists("task1_completed")) {
                break;
            }
            check_counter = 0;
        }

        MetricRecord* record = &args->buffer[args->samples_collected];
        
        // Get temperature
        result = nvmlDeviceGetTemperature(args->device, NVML_TEMPERATURE_GPU, &record->temp);
        if (NVML_SUCCESS != result) {
            printf("Failed to get temperature for GPU %u: %s\n", args->gpu_index, nvmlErrorString(result));
            continue;
        }

        // Get clock speed
        result = nvmlDeviceGetClockInfo(args->device, NVML_CLOCK_GRAPHICS, &record->clock);
        if (NVML_SUCCESS != result) {
            printf("Failed to get clock speed for GPU %u: %s\n", args->gpu_index, nvmlErrorString(result));
            continue;
        }

        // Get power usage
        unsigned int power;
        result = nvmlDeviceGetPowerUsage(args->device, &power);
        if (NVML_SUCCESS != result) {
            printf("Failed to get power usage for GPU %u: %s\n", args->gpu_index, nvmlErrorString(result));
            continue;
        }
        record->power = power / 1000.0;  // Convert to watts
        record->timestamp = current_time_ns();
        
        args->samples_collected++;

        // Calculate next sample time
        next_sample_time += SAMPLE_INTERVAL_MS * 1000000LL; // Convert to nanoseconds
        precise_sleep(next_sample_time);
    }

    return NULL;
}

int main() {
    nvmlReturn_t result;
    unsigned int device_count;
    char hostname[256];
    pthread_t* threads;
    ThreadArgs* thread_args;
    MetricRecord** gpu_buffers;

    // Get the hostname from the environment variable HOST_HOSTNAME
    const char* env_hostname = getenv("HOST_HOSTNAME");
    if (env_hostname != NULL) {
        strncpy(hostname, env_hostname, sizeof(hostname) - 1);
        hostname[sizeof(hostname) - 1] = '\0'; // Ensure null-termination
    } else {
        fprintf(stderr, "Environment variable HOST_HOSTNAME not set\n");
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
    }

    // Allocate resources
    threads = (pthread_t*)malloc(device_count * sizeof(pthread_t));
    thread_args = (ThreadArgs*)malloc(device_count * sizeof(ThreadArgs));
    gpu_buffers = (MetricRecord**)malloc(device_count * sizeof(MetricRecord*));

    if (!threads || !thread_args || !gpu_buffers) {
        printf("Failed to allocate memory for control structures\n");
        return 1;
    }

    // Allocate fixed-size buffer for each GPU
    for (unsigned int i = 0; i < device_count; i++) {
        gpu_buffers[i] = (MetricRecord*)malloc(MAX_SAMPLES * sizeof(MetricRecord));
        if (gpu_buffers[i] == NULL) {
            printf("Failed to allocate memory for GPU %u\n", i);
            return 1;
        }
    }

    // Create monitoring thread for each GPU
    for (unsigned int gpu_index = 0; gpu_index < device_count; ++gpu_index) {
        // Get the GPU device handle
        result = nvmlDeviceGetHandleByIndex(gpu_index, &thread_args[gpu_index].device);
        if (NVML_SUCCESS != result) {
            printf("Failed to get handle for device %u: %s\n", gpu_index, nvmlErrorString(result));
            continue;
        }

        // Set thread parameters
        thread_args[gpu_index].gpu_index = gpu_index;
        strcpy(thread_args[gpu_index].hostname, hostname);
        thread_args[gpu_index].buffer = gpu_buffers[gpu_index];

        // Create thread
        if (pthread_create(&threads[gpu_index], NULL, monitor_gpu, &thread_args[gpu_index]) != 0) {
            printf("Failed to create thread for GPU %u\n", gpu_index);
            continue;
        }
    }

    // Wait for all threads to complete
    for (unsigned int i = 0; i < device_count; ++i) {
        pthread_join(threads[i], NULL);
    }

    // Write data to files
    for (unsigned int gpu_index = 0; gpu_index < device_count; ++gpu_index) {
        char filename[256];
        snprintf(filename, sizeof(filename), "gpu_metrics%u.txt", gpu_index);
        FILE *file = fopen(filename, "w");
        if (!file) {
            printf("Failed to open file %s for writing\n", filename);
            continue;
        }

        // Write all collected data for this GPU
        for (int i = 0; i < thread_args[gpu_index].samples_collected; ++i) {
            MetricRecord* record = &gpu_buffers[gpu_index][i];
            fprintf(file, "gpu_metrics,host=%s,gpu=%u temp=%u,clock_speed=%u,power=%.2f %lld\n",
                    hostname, gpu_index, record->temp, record->clock, record->power, record->timestamp);
        }

        fclose(file);
    }

    // Cleanup resources
    for (unsigned int i = 0; i < device_count; i++) {
        free(gpu_buffers[i]);
    }
    free(gpu_buffers);
    free(threads);
    free(thread_args);

    // Shutdown NVML
    nvmlShutdown();
    return 0;
}