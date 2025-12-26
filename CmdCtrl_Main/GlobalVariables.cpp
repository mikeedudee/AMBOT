#include "GlobalVariables.h"

// --- CONSTANTS ---
const char* LOG_FILENAME          = "motor_log.csv";
const int               MAX_CMD_LEN           = 32;

// --- FLAGS & STATE ---
bool                    isSDReady             = false;
int                     save_data_state       = 1;
int                     show_data_state       = 1;
bool                    serialCommunicationFlag = false;
bool                    isLeftMotorActive     = false;
bool                    isRightMotorActive    = false;
bool                    failsafeTriggered     = false;

// --- TIMERS ---
unsigned long           lastCommandTime       = 0;
unsigned long           FAILSAFE_TIMEOUT      = 500; // 0.5 Seconds
unsigned long           lastMotorTime         = 0;
unsigned long           lastServoTime         = 0;

// --- BUFFERS ---
char                    usbBuffer[32]; // Size must match MAX_CMD_LEN
int                     usbIndex              = 0;
char                    radioBuffer[32];
int                     radioIndex            = 0;
char                    servoCommands[6]      = {0,0,0,0,0,0}; // NumServos = 6

// --- OBJECTS ---
SdFs                    sd;
FsFile                  logFile;
WDT_T4<WDT1>            wdt;
LedController           ledSys;

// Motor Pins: RPWM, LPWM, R_EN, L_EN
Motor                   leftMotor(2, 3, 21, 20);
Motor                   rightMotor(5, 6, 22, 23);
ServoController         controller;