// GlobalVariables.cpp
#include "GlobalVariables.h"

/// BAROMETER DEFAULTS
double                      referencePressure           = 0.0;
double                      realTemperature             = 0.0;
long                        realPressure                = 0.0F;
float                       absoluteAltitude            = 0.0F;
float                       relativeAltitude            = 0.0F;
double                      Altitude_Filtered           = 0.0;

// VELOCITY
float                       previousAltitude            = 0.0F;
unsigned long               previousTime                = 0.0F;
float                       Vertical_Velocity           = 0.0F;
unsigned long               present                     = 0.0F;

// --- NEW: GROUND VELOCITY ---
float                       GPS_Speed_Kmph              = 0.0F;
float                       GPS_Speed_Mps               = 0.0F;
float                       IMU_Accel_X                 = 0.0F;
float                       IMU_Accel_Y                 = 0.0F;
float                       IMU_Speed_X                 = 0.0F;

// THERMISTOR
float                       Analog_to_Voltage           = 0.0F;
float                       Resistance_Therm            = 0.0F;
float                       Temperature_Therm           = 0.0F;

// GPS
float                       GPS_Latitude                = 0.0F;
float                       GPS_Longitude               = 0.0F; 
float                       GPS_Altitude                = 0.0F;
float                       GPS_Latitude_Init           = 0.0F;
float                       GPS_Longitude_Init          = 0.0F;
float                       GPS_DistanceBetween         = 0.0F;

// TIME
unsigned long               Time_Elapsed                = 0.0;
unsigned long               previous_millis             = 0.0;

// IMU (9-DoF)
double                      Yaw_Output                  = 0.0;
double                      Pitch_Output                = 0.0;
double                      Roll_Output                 = 0.0;
double                      nowLast                     = 0.0;
int                         sensorStatusValue           = 1;

// KALMAN FILTER INSTANCE
double Altitude_kalt_Filtered                           = 0.0;

// ALARM LIGHTS
int                         stateLED_MS5611             = 0;
int                         stateLED_BNO                = 0;
bool                        stateLED_Main               = false;
bool                        state_Buzzer                = false;
bool                        Manual_Override             = false;

// SD CARD STATE
int                         SDCard_Status               = 0;
int                         save_data_state             = 1;
int                         show_data_state             = 1;
const char* filename                    = "data.csv"; 

// SD CARD OBJECTS
SdFs sd;
FsFile file;

// Non-blocking Iterator
unsigned long               prevLogTime                 = 0.0;

// --- NEW: FILTERED VALUES ---
float                       Filtered_Accel_X            = 0.0F;
float                       Filtered_GPS_Speed          = 0.0F;

// WATCHDOG TIMER INSTANCE
WDT_T4<WDT1> wdt;

// START UP FLAG APC COMMUNICATION
bool                        APC_Flag_Connection         = false;