#ifndef GLOBALVARIABLES_H
#define GLOBALVARIABLES_H

// MS5611
extern double                       referencePressure;
extern double                       realTemperature;
extern long                         realPressure;
extern float                        absoluteAltitude;
extern float                        relativeAltitude;
extern double                       Altitude_Filtered;

// IMU (9-DoF)
extern double                       sensor_status;
extern double                       Yaw_Output;
extern double                       Pitch_Output;
extern double                       Roll_Output;
extern double                       nowLast;
extern int                          sensorStatusValue;
extern float                        Heading_Compass;
extern float                        Heading_True;

// THERMISTOR
extern float                        Temperature_Therm;
static constexpr float              THERMISTOR_TEMP_INIT            = 298.15F;
static constexpr int                THERMISTOR_R0                   = 10000;        
static constexpr int                THERMISTOR_BETA                 = 3435;

// GPS
extern float                         LATITUDE;
extern float                         LONGITUDE;
extern float                         ALTITUDE;
extern float                         TIME_HOUR;
extern float                         TIME_MINUTE;
extern float                         TIME_SECOND;

extern int                           MS5611_STATUS;
extern int                           GPS_STATUS;
extern int                           IMU_STATUS;
extern int                           THERMISTOR_STATUS;
extern int                           APC220_STATUS;

#endif