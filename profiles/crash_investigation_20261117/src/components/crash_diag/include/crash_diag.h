#pragma once
/* DIAGNOSTIC ONLY - never used for timing or reliability measurements. */
#ifdef __cplusplus
extern "C" {
#endif
#ifndef CRASH_DIAG_MODE
#define CRASH_DIAG_MODE 0
#endif
#ifndef CRASH_DIAG_CHECKPOINTS
#define CRASH_DIAG_CHECKPOINTS 1
#endif
void crash_diag_banner(void);
void crash_diag_checkpoint(const char *name);
void crash_diag_heap(const char *stage);
void crash_diag_stacks(const char *stage);
void crash_diag_note(const char *tag, unsigned a, unsigned b, unsigned c);
#ifdef __cplusplus
}
#endif
