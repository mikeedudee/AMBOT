#include <Arduino.h>
#include "imxrt.h"
#include <MS5611.h>
#include <SoftwareSerial.h>
#include <Adafruit_BNO08x.h>
#include <math.h>
#include <Wire.h>
#include <TinyGPS++.h>

// LOAD ALL THE GLOBAL VARIABLES AND DATA LOGGER
#include "GlobalVariables.h"

#define       DECLINATION     1f
unsigned long Heading_Valid   = 0;

#define       DECLINATION     1.2f
#define       BNO08X_I2C_ADDR 0x4B

#define       GPS_Serial      Serial1
#define       GPSBaud         9600

#define       APC220          Serial2
#define       APC_BAUD        9600

MS5611      ms5611;
TinyGPSPlus gps;

Adafruit_BNO08x bno08x(BNO08X_I2C_ADDR);
sh2_SensorValue_t sensorValue;

typedef struct {
    float yaw;
    float pitch;
    float roll;
} euler_t;

euler_t ypr;


void setup() {
    Serial.begin(115200);
    APC220.begin(APC_BAUD);
    Wire.begin();
    while (!Serial) { delay(10); }
    delay(100);
    MS5611_Init();
    delay(100);
    IMU_Init();
    delay(100);
    GPS_INIT();
    //analogReadResolution(12);

}

void loop() {
  MS5611_CORE();
  IMU_CORE();
  THERMISTOR_CORE();
  GPS_CORE();

  // FORMAT:
  // Temperature, Pressure, Absolute Altitude, Filtered Altitude, Yaw, Pitch, Roll, Heading, BNO Sensor Calibration Status,
  // Temperature Thermistor, Latitude, Longitude, Altitude, Time Hour, Time Minute, Time Second,
  // GPS_STATUS, MS5611_STATUS, THERMISTOR_STATUS

  char buffer_data[256];  // Increased size to safely hold all data

  snprintf(buffer_data, sizeof(buffer_data),
          "%.2f %ld %.2f %.2f %.2f %.2f %.2f %.2f %d %.2f %.6f %.6f %.2f %d %d %d",
          realTemperature,          // Temperature from MS5611
          realPressure,             // Pressure
          absoluteAltitude,         // Absolute Altitude
          Altitude_Filtered,        // Filtered Altitude
          Yaw_Output,               // Yaw
          Pitch_Output,             // Pitch
          Roll_Output,              // Roll
          Heading_True,             // Heading
          sensorStatusValue,        // BNO Sensor Calibration (assuming int)
          Temperature_Therm,        // Thermistor Temperature
          LATITUDE,                 // GPS Latitude
          LONGITUDE,                // GPS Longitude
          ALTITUDE,                 // GPS Altitude
          TIME_HOUR,                // Time Hour
          TIME_MINUTE,              // Time Minute
          TIME_SECOND              // Time Second
  );

    Serial.print(buffer_data);
    Serial.print(" ");
    Serial.print(GPS_STATUS);
    Serial.print(" ");
    Serial.print(MS5611_STATUS);
    Serial.print(" ");
    Serial.println(THERMISTOR_STATUS);

    APC220.println(buffer_data);

}
