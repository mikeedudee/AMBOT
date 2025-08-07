#include "GlobalVariables.h"

/// BAROMETER DEFAULTS
// MS5611
double                      referencePressure           = 0.0;
double                      realTemperature             = 0.0;
long                        realPressure                = 0.0F;
float                       absoluteAltitude            = 0.0F;
float                       relativeAltitude            = 0.0F;
double                      Altitude_Filtered           = 0.0;

// IMU (9-DoF)
double                      Yaw_Output                  = 0.0;
double                      Pitch_Output                = 0.0;
double                      Roll_Output                 = 0.0;
double                      nowLast                     = 0.0;
int                         sensorStatusValue           = 1;
float                       Heading_Compass             = 0.0f;
float                       Heading_True                = 0.0f;

// THERMISTOR
float                       Temperature_Therm           = 0.0F;

// GPS
float                       LATITUDE                    = 0.0F;
float                       LONGITUDE                   = 0.0F;
float                       ALTITUDE                    = 0.0F;
float                       TIME                        = 0.0F;
float                       TIME_HOUR                   = 0.0F;
float                       TIME_MINUTE                 = 0.0F;
float                       TIME_SECOND                 = 0.0F;

// SENSOR VALIDATORS
int                         MS5611_STATUS               = 0;
int                         GPS_STATUS                  = 0;
int                         IMU_STATUS                  = 0;
int                         THERMISTOR_STATUS           = 0;
int                         APC220_STATUS               = 0;