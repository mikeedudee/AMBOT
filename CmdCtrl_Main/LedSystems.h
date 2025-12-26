#ifndef LED_SYSTEMS_H
#define LED_SYSTEMS_H

#include <Arduino.h>

// --- PIN DEFINITIONS ---
const int PIN_SCANNER[]   = { 10, 11 }; 
const int PIN_FAST_BLINK  = 24;
const int PIN_SEQUENCE    = 9;
const int PIN_HEARTBEAT   = 13;

// --- SETTINGS ---
const int SCAN_SPEED      = 100;
const int PIN24_SPEED     = 50;
const int HEARTBEAT_SPEED = 500;

class LedController {
private:
    // Scanner Variables
    unsigned long lastScanTime  = 0;
    int scannerIdx              = 0;
    int scannerDir              = 1;
    int scannerStep             = 0;

    // Beacon Variables
    unsigned long lastBeaconTime    = 0;
    int beaconStep                  = 0;
    
    // Simple Blinker Variables
    bool s24        = false; unsigned long t24      = 0;
    bool s13        = false; unsigned long t13      = 0;
    bool sSingle    = false; unsigned long tSingle  = 0; 

public:
    void begin() {
        pinMode(PIN_FAST_BLINK, OUTPUT);
        pinMode(PIN_SEQUENCE, OUTPUT);
        pinMode(PIN_HEARTBEAT, OUTPUT);
        for (int p : PIN_SCANNER) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
    }

    // Main Update Function
    void update(bool leftMotorActive, bool rightMotorActive, bool servoActive, bool commsActive) {
        unsigned long currentMillis = millis();

        // 1. Run Heartbeat (Always Running)
        runSimpleBlinker(PIN_HEARTBEAT, HEARTBEAT_SPEED, currentMillis, s13, t13);
        
        // 2. Fast Blink (Pin 24) - ONLY if Comms Active
        if (commsActive) { 
            runSimpleBlinker(PIN_FAST_BLINK, PIN24_SPEED, currentMillis, s24, t24);
        } else {
            digitalWrite(PIN_FAST_BLINK, LOW); // Force OFF if no comms
        }
        
        // 3. Run Scanner Logic (Pins 10 & 11) based on Motors
        runScannerLogic(currentMillis, leftMotorActive, rightMotorActive);

        // 4. Run Beacon Logic (Pin 9) based on Servo Controller
        runBeaconLogic(currentMillis, servoActive);
    }

private:
    void runSimpleBlinker(int pin, int speed, unsigned long now, bool &state, unsigned long &lastTime) {
        if (now - lastTime >= speed) {
            lastTime    = now;
            state       = !state;
            digitalWrite(pin, state);
        }
    }

    void runBeaconLogic(unsigned long now, bool isConnected) {
        if (!isConnected) {
            digitalWrite(PIN_SEQUENCE, HIGH); 
            beaconStep = 1; 
            return;
        }
        const int BLINK_SPEED = 100; 
        if (now - lastBeaconTime >= BLINK_SPEED) {
            lastBeaconTime  = now;
            beaconStep      = !beaconStep; 
            digitalWrite(PIN_SEQUENCE, beaconStep);
        }
    }

    void runScannerLogic(unsigned long now, bool leftActive, bool rightActive) {
        if (!leftActive && !rightActive) {
            digitalWrite(PIN_SCANNER[0], LOW);
            digitalWrite(PIN_SCANNER[1], LOW);
            return;
        }

        if (leftActive && rightActive) {
            if (now - lastScanTime < SCAN_SPEED) return;
            lastScanTime = now;

            if (scannerStep == 0 || scannerStep == 2) {
                digitalWrite(PIN_SCANNER[scannerIdx], HIGH);
            } else if (scannerStep == 1) {
                digitalWrite(PIN_SCANNER[scannerIdx], LOW);
            } else if (scannerStep == 3) {
                digitalWrite(PIN_SCANNER[scannerIdx], LOW); 
                int next = scannerIdx + scannerDir;
                if (next >= 2) { scannerDir = -1; scannerIdx = 0; }
                else if (next < 0) { scannerDir = 1; scannerIdx = 1; }
                else scannerIdx = next;
                digitalWrite(PIN_SCANNER[scannerIdx], HIGH);
                scannerStep = 0;
                return;
            }
            scannerStep++;
            return;
        }

        if (leftActive && !rightActive) {
            digitalWrite(PIN_SCANNER[1], LOW); 
            runSimpleBlinker(PIN_SCANNER[0], SCAN_SPEED, now, sSingle, tSingle);
        }

        if (!leftActive && rightActive) {
            digitalWrite(PIN_SCANNER[0], LOW); 
            runSimpleBlinker(PIN_SCANNER[1], SCAN_SPEED, now, sSingle, tSingle);
        }
    }
};

#endif