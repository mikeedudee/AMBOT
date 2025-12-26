// GlobalVariables.h
#ifndef GLOBALVARIABLES_H
#define GLOBALVARIABLES_H

#include <SdFat.h>
#include <Watchdog_t4.h>

// SD CARD OBJECTS
extern SdFs sd;
extern FsFile file;

// MS5611
extern double                       referencePressure;
extern double                       realTemperature;
extern long                         realPressure;
extern float                        absoluteAltitude;
extern float                        relativeAltitude;
extern double                       Altitude_Filtered;

// VELOCITY (Vertical)
extern float                        previousAltitude;
extern unsigned long                previousTime;
extern float                        Vertical_Velocity;

// --- NEW: GROUND VELOCITY (Horizontal) ---
extern float                        GPS_Speed_Kmph;     // Speed from GPS
extern float                        GPS_Speed_Mps;      // Speed in m/s
extern float                        IMU_Accel_X;        // Linear Accel X (Forward/Backward)
extern float                        IMU_Accel_Y;        // Linear Accel Y (Sideways)
extern float                        IMU_Speed_X;        // Integrated Speed X (High Drift)

// THERMISTOR
static constexpr float              THERMISTOR_TEMP_INIT            = 298.15F;
static constexpr int                THERMISTOR_R0                   = 10000;        
static constexpr int                THERMISTOR_BETA                 = 3435;
extern float                        Analog_to_Voltage;
extern float                        Resistance_Therm;
extern float                        Temperature_Therm;

// GPS CONFIGURATION
static constexpr int                RXPin                           = 0;
static constexpr int                TXPin                           = 1;
// CRITICAL: Increased to 115200 to handle 10Hz data stream from Neo M10
static constexpr uint32_t           GPSBaud                         = 115200; 

extern float                        GPS_Latitude;
extern float                        GPS_Longitude;
extern float                        GPS_Altitude;       
extern float                        GPS_Latitude_Init;
extern float                        GPS_Longitude_Init;       
extern float                        GPS_DistanceBetween;     

// TIME
extern unsigned long                Time_Elapsed;
extern unsigned long                previous_millis;

// IMU (9-DoF)
extern double                       sensor_status;
extern double                       Yaw_Output;
extern double                       Pitch_Output;
extern double                       Roll_Output;
extern double                       nowLast;
extern int                          sensorStatusValue;

// KALMAN FILTER INSTANCE
extern double                       Altitude_kalt_Filtered;

// ALARM LIGHTS
extern int                          stateLED_MS5611;
extern int                          stateLED_BNO;
extern bool                         stateLED_Main;
extern bool                         state_Buzzer;
extern bool                         Manual_Override;
static constexpr unsigned long      TOGGLING_INTERVAL               = 250UL;

// SD CARD STATE
extern int                          SDCard_Status;
extern int                          save_data_state;
extern int                          show_data_state;
extern const char* filename;

// Non-blocking Iterator
extern unsigned long                prevLogTime;
static constexpr int                logGap                         = 0;
extern unsigned long                present;

// --- NEW: FILTERED VALUES & CONSTANTS ---
extern float                        Filtered_Accel_X;   // Smoothed Acceleration
extern float                        Filtered_GPS_Speed; // Smoothed GPS Speed

// FILTER STRENGTH (Alpha)
// 0.1 = Very Slow/Smooth (High Lag)
// 0.5 = Balanced
// 0.8 = Fast/Responsive (More Noise)
static constexpr float              FILTER_ALPHA = 0.2f;

// WATCHDOG TIMER
// WDT1 is the standard hardware watchdog on Teensy 4.1
extern                              WDT_T4<WDT1> wdt;

// START UP FLAG APC COMMUNICATION
extern bool                         APC_Flag_Connection;

#endif