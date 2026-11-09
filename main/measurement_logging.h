#ifndef MEASUREMENT_LOGGING_H
#define MEASUREMENT_LOGGING_H

/* Logging-only experiment switch. Set to 0 to restore verbose diagnostics. */
#define QUIET_MEASUREMENT 1

#if QUIET_MEASUREMENT
#define MEASUREMENT_LOGI(...) ((void)0)
#define MEASUREMENT_LOGD(...) ((void)0)
#else
#define MEASUREMENT_LOGI(...) ESP_LOGI(__VA_ARGS__)
#define MEASUREMENT_LOGD(...) ESP_LOGD(__VA_ARGS__)
#endif

#endif
