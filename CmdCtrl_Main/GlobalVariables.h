#ifndef GLOBALVARIABLES_H
#define GLOBALVARIABLES_H

#include <Arduino.h>
#include <SdFat.h>
#include <Watchdog_t4.h>
#include "MotorDriver.h"
#include "ServoController.h"
#include "LedSystems.h"

// --- CONSTANTS ---
extern const char* LOG_FILENAME;
extern const int        MAX_CMD_LEN;

// --- FLAGS & STATE ---
extern bool             isSDReady;
extern int              save_data_state;
extern int              show_data_state;
extern bool             serialCommunicationFlag;
extern bool             isLeftMotorActive;
extern bool             isRightMotorActive;
extern bool             failsafeTriggered;

// --- TIMERS ---
extern unsigned long    lastCommandTime;
extern unsigned long    FAILSAFE_TIMEOUT;
extern unsigned long    lastMotorTime;
extern unsigned long    lastServoTime;

// --- BUFFERS ---
extern char             usbBuffer[];
extern int              usbIndex;
extern char             radioBuffer[];
extern int              radioIndex;
extern char             servoCommands[];

// --- OBJECTS ---
extern SdFs             sd;
extern FsFile           logFile;
extern WDT_T4<WDT1>     wdt;
extern LedController    ledSys;
extern Motor            leftMotor;
extern Motor            rightMotor;
extern ServoController  controller;

#endif