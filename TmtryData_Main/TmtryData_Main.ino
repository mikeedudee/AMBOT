  /**
 * ROVER TELEMETRY SYSTEM
 * Architecture: Non-Blocking Loop with Watchdog Safety
 * Target: Teensy 4.1
 * Standard: NASA Power of Ten / JSF C++
 */

// --- SYSTEM LIBRARIES ---
#include <Arduino.h>
#include "imxrt.h"          // Teensy 4.1 hardware registers
#include <Wire.h>           // I2C Communication
#include <MS5611.h>         // Barometer Library
#include <SimpleKalmanFilter.h>
#include <TinyGPS++.h>      // NMEA Parsing
#include <SoftwareSerial.h> // (Backup, not used for main GPS)
#include <Adafruit_BNO08x.h> // IMU Library
#include <SdFat.h>          // High-performance SDIO Library
#include <math.h>

// --- CUSTOM MODULES ---
#include "GlobalVariables.h" // Shared variables across files
#include "SDCardLogger.h"    // Safe SD Card Class
#include "SystemCodes.h"     // Numeric Status Codes (e.g., 001000)

// --- HARDWARE SERIAL CONFIGURATION ---
// Critical: Neo M10 requires Hardware Serial (Serial1), not SoftwareSerial
#define   GPSSerial     Serial2
// Note: GPSBaud is defined as 115200 in GlobalVariables.h

// --- RADIO CONFIGURATION ---
// APC220 Module for Ground Telemetry
#define   APC220        Serial1
#define   APC_BAUD      9600

// --- SENSOR OBJECTS ---
MS5611                ms5611;
TinyGPSPlus           gps;

// --- PIN DEFINITIONS ---
// Pin 13 (Builtin) = Heartbeat/Status
// Pin 24 = External Status LED
static constexpr int      LED_OUTPUT_PINS[]     = { LED_BUILTIN, 24};
static constexpr size_t   LED_NUM_OUTPUT_PINS   = sizeof(LED_OUTPUT_PINS)/sizeof(LED_OUTPUT_PINS[0]);

// --- NON-BLOCKING TIMER VARIABLES ---
static unsigned long      prevPin24Time         = 0;
static bool               pin24State            = false;
const int                 SCAN_SPEED            = 50;   // Pin 24 Blink Speed (ms)
static bool               builtinState          = true;

// --- IMU CONFIGURATION ---
#define   BNO08X_RESET  -1
struct euler_t {
  float yaw;
  float pitch;
  float roll;
} ypr;

Adafruit_BNO08x         bno08x(BNO08X_RESET);
sh2_SensorValue_t       sensorValue;

// IMU Report Rate Configuration
#ifdef FAST_MODE
  sh2_SensorId_t  reportType          = SH2_GYRO_INTEGRATED_RV;
  long            reportIntervalUs    = 2000; // 500Hz
#else
  sh2_SensorId_t  reportType          = SH2_ARVR_STABILIZED_RV;
  long            reportIntervalUs    = 5000; // 200Hz
#endif

// Helper: Enable IMU Reports
void setReports(sh2_SensorId_t reportType, long report_interval) {
  if (! bno08x.enableReport(reportType, report_interval)) {}
}

/**
 * TELEMETRY TRANSMITTER
 * Sends a 6-digit status code to USB, Radio, and SD Card.
 * Example: transmitCode(1000) -> sends "001000"
 */
void transmitCode(uint16_t code) {
  char codeBuffer[8];
  // Safety: snprintf prevents buffer overflow
  snprintf(codeBuffer, sizeof(codeBuffer), "%06d", code);
  
  print_data(codeBuffer);
  logger.logValue(codeBuffer);
}

/**
 * WATCHDOG WARNING INTERRUPT ("The Scream")
 * Triggered if the CPU hangs for 2.5 seconds.
 * Gives a final warning before the hard reset at 5.0 seconds.
 */
void wdtWarning() {
  print_data("005011");     // Log Code: Watchdog Warning
  logger.logValue("005011"); 

  // Emergency: Turn on ALL LEDs to indicate freeze
  for (size_t i = 0; i < LED_NUM_OUTPUT_PINS; i++) {
         pinMode(LED_OUTPUT_PINS[i], OUTPUT);
         digitalWrite(LED_OUTPUT_PINS[i], HIGH);
    }
}

/**
 * RESET CAUSE CHECKER ("The Post-Mortem")
 * Checks hardware registers to see if the last reboot was caused by a crash.
 */
void checkResetCause() {
  // SRC_SRSR Register Bit 5 (0x20) = Watchdog Reset
  if (SRC_SRSR & 0x20) {
    transmitCode(ERR_WATCHDOG_RESET); // Send "005010" (I crashed!)
  } else {
    transmitCode(SYS_BOOT_START);     // Send "001000" (Normal Boot)
  }
  // Clear register for next time
  SRC_SRSR = 0xFFFFFFFF;
}

// ================================================================
// SYSTEM SETUP
// ================================================================
void setup() {
    // Initialize Serial Communication
    Serial.begin(115200);
    APC220.begin(APC_BAUD);
    // Wait for Serial Monitor (Max 3 seconds) so we don't miss startup logs
    unsigned long startWait = millis();
    while (!Serial && (millis() - startWait < 3000) && !APC220) { 
      delay(10);
      APC_Flag_Connection = false; 
    }
    APC_Flag_Connection = true;
    
    // Diagnostics: Check why we are booting
    checkResetCause();

    // Configure Hardware Pins
    analogReadResolution(12); // High precision for Thermistor (0-4095)

    for (size_t i = 0; i < LED_NUM_OUTPUT_PINS; i++) {
         pinMode(LED_OUTPUT_PINS[i], OUTPUT);
         digitalWrite(LED_OUTPUT_PINS[i], LOW);
    }
    digitalWrite(LED_OUTPUT_PINS[0], HIGH); // LED ON = Booting
    
    // NOTE: Watchdog is NOT enabled yet. 
    // We intentionally wait until sensors are initialized to prevent 
    // "false Positive" freeze detection during the slow boot process.

    transmitCode(SENS_INIT_START); // "002000"

    // Initialize SD Card (Critical System)
    if (!logger.begin()) {
        transmitCode(ERR_SD_INIT_FAIL); // "005001"
        // Visual Error Code: 3 Long Blinks
        for(int i = 0; i < 3; i++) {
             digitalWrite(LED_OUTPUT_PINS[1], HIGH); delay(500); 
             digitalWrite(LED_OUTPUT_PINS[1], LOW);  delay(500);
        }
    } else {
        transmitCode(SENS_SD_OK); // "002001"
    }

    // Initialize Sensors (This takes ~3-4 seconds total)
    delay(100);
    MS5611_Init();
    delay(100);
    IMU_Init();
    delay(100);
    GPS_Init(); // Note: This includes the Neo M10 handshake (slow)
    
    transmitCode(SYS_BOOT_COMPLETE); // "001001"
    digitalWrite(LED_OUTPUT_PINS[0], LOW); // LED OFF = Ready
    Serial.print("\n");

    // ARM SAFETY SYSTEM (Watchdog)
    // Now that boot is done, we start the 5-second timer.
    WDT_timings_t config;
    config.timeout    = 5000;       // Hard Reset after 5s silence
    config.trigger    = 2500;       // Warning Interrupt after 2.5s silence
    config.callback   = wdtWarning; // Link the warning function
    wdt.begin(config);
}

// ================================================================
// MAIN LOOP
// ================================================================
void loop() {
  // SAFETY: Feed the Watchdog
  // Tells hardware: "I am alive. Reset the 5-second timer."
  wdt.feed();

  present = millis();

  // 1. DATA ACQUISITION
  // These functions read raw data and update GlobalVariables
  MS5611_CORE();
  IMU_CORE();
  GPS_CORE();
  THERMISTOR_CORE();

  // 2. INDEPENDENT TASK: Fast Blink (Pin 24)
  // Visual indicator that the loop is running fast
  if ((present - prevPin24Time >= SCAN_SPEED) && (APC_Flag_Connection == true)) {
      prevPin24Time = present;
      pin24State    = !pin24State;
      digitalWrite(LED_OUTPUT_PINS[1], pin24State);
  } else {
    digitalWrite(LED_OUTPUT_PINS[1], 0);
  }

  // 3. INDEPENDENT TASK: Telemetry Logging
  // Runs at 0ms real-time
  if (present - prevLogTime >= logGap) {
    prevLogTime   = present;
    
    // Toggle Heartbeat LED
    builtinState  = !builtinState; 
    digitalWrite(LED_OUTPUT_PINS[0], builtinState);

    doTelemetry();
  }
}

/**
 * TELEMETRY FORMATTER
 * Formats data into CSV string and saves to SD/Radio
 */
void doTelemetry() {
    // Update derived calculations
    Time_Elapsed              = millis() / 1000;
    Vertical_Velocity         = ms5611.getVelocity(Altitude_Filtered, present);
    float AverageTemperature  = (realTemperature + Temperature_Therm) / 2.0f;

    char buffer[256]; // Large buffer to prevent overflow
    
    // CSV FORMAT SPECIFICATION:
    // 1. TimeMs (System Uptime)
    // 2. Pressure (Pa)
    // 3. Alt (Filtered Meters)
    // 4. Temp (Barometer C)
    // 5. ThermTemp (Thermistor C)
    // 6. AvgTemp (C)
    // 7. Lat (Decimal Degrees)
    // 8. Lon (Decimal Degrees)
    // 9. SDStat (1=OK, 0=Fail)
    // 10. TimeSec (Seconds)
    // 11. SensorStat (IMU Confidence 0-3)
    // 12. Yaw (Heading)
    // 13. Pitch (Tilt)
    // 14. Roll (Bank)
    // 15. VertVel (m/s)
    // 16. AbsAlt (ASL)
    // 17. GPS_Speed (m/s - Filtered)
    // 18. IMU_Speed (m/s - Integrated)
    
    int len = snprintf(buffer, sizeof(buffer), 
        "%lu, %ld, %.4f, %.4f, %.4f, %.4f, %.8f, %.8f, %d, %lu, %d, %.6f, %.6f, %.6f, %.4f, %.4f, %.4f, %.4f", 
        present,            
        realPressure,
        Altitude_Filtered,
        realTemperature, 
        Temperature_Therm,
        AverageTemperature,
        GPS_Latitude,
        GPS_Longitude,
        SDCard_Status,
        Time_Elapsed,       
        sensorStatusValue,
        Yaw_Output,
        Pitch_Output,
        Roll_Output,
        Vertical_Velocity,
        absoluteAltitude,
        Filtered_GPS_Speed,   
        IMU_Speed_X           
    );
  
    // Verify formatting success before writing
    if (len > 0 && len < (int)sizeof(buffer)) {
        print_data(buffer);       // Send to Serial/Radio
        logger.logValue(buffer);  // Save to SD Card
    }
}