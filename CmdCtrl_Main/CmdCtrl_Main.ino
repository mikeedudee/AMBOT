/**
 * ROVER MOTOR CONTROLLER - ACTUATOR NODE (SILENT MODE)
 * Target: Teensy 4.1
 */

#include <Wire.h>
#include "GlobalVariables.h"
#include "SystemCodes.h" 

// RADIO CONFIGURATION (RX ONLY)
#define APC220 Serial1
#define APC_BAUD 9600

const unsigned long MOTOR_INTERVAL = 10;
const unsigned long SERVO_INTERVAL = 20;

// --- HELPER: LOG TO SD (Non-Blocking Attempt) ---
void logToSD(const char* data) {
    if (!isSDReady) return;
    // Open, Write, Sync
    logFile = sd.open(LOG_FILENAME, O_RDWR | O_CREAT | O_APPEND);
    if (logFile) {
        logFile.println(data);
        logFile.close();
    }
}

// --- HELPER: Transmit/Log Code (SILENT VERSION) ---
void transmitCode(uint16_t code) {
  char codeBuffer[16];
  // Format: "Uptime,Code"
  snprintf(codeBuffer, sizeof(codeBuffer), "%lu,%06d", millis(), code);
  logToSD(codeBuffer);
}

// --- COMMAND PARSING ---
void processCommand(char* cmd) {
    // Reset Failsafe Timer
    lastCommandTime = millis();
    if(failsafeTriggered) {
        failsafeTriggered = false;
        transmitCode(SAFE_FAILSAFE_CLEAR);
    }

    // 1. SERVO COMMAND (Starts with 'S')
    if (cmd[0] == 'S') {
        int idx = cmd[1] - '1';
        char dir = cmd[2];
        if (idx >= 0 && idx < ServoController::numServos) {
            servoCommands[idx] = (dir == 'L' || dir == 'R') ? dir : 0;
        }
    }
    // 2. MOTOR COMMAND (Numbers)
    else {
        char* token = strtok(cmd, ",");
        if (token != NULL) {
            int leftVal = atoi(token);
            token = strtok(NULL, ",");
            if (token != NULL) {
                int rightVal = atoi(token);
                leftMotor.setTarget(leftVal);
                rightMotor.setTarget(rightVal);
                
                isLeftMotorActive = (leftVal != 0);
                isRightMotorActive = (rightVal != 0);
            }
        }
    }
}

// --- HELPER: Read Input Stream ---
void checkInput(Stream &stream, char* buffer, int &index) {
    while (stream.available() > 0) {
        char c = stream.read();
        if (c == '\n' || c == '\r') {
            if (index > 0) {
                buffer[index] = '\0'; // Null-terminate
                processCommand(buffer);
                index = 0; // Reset
            }
        } else {
            if (index < MAX_CMD_LEN - 1) {
                buffer[index++] = c;
            }
        }
    }
}

// --- SETUP ---
void setup() {
    // 1. Initialize Communication
    // APC220 (UART) does not return a status bool, so we just init it.
    APC220.begin(APC_BAUD); 
    Serial.begin(115200);
    
    // Set flag to true now that comms have begun
    serialCommunicationFlag = true;

    // 2. Initialize SD Card
    if (sd.begin(SdioConfig(FIFO_SDIO))) {
        isSDReady = true;
        logToSD("--- NEW SESSION ---");
    } else {
        isSDReady = false;
    }

    // 3. Check Reset Cause
    if (SRC_SRSR & 0x20) transmitCode(ERR_WATCHDOG_RESET);
    else transmitCode(SYS_BOOT_START);
    SRC_SRSR = 0xFFFFFFFF;

    transmitCode(ACT_INIT_START);
    
    // 4. Hardware Init
    leftMotor.begin();
    rightMotor.begin();
    transmitCode(ACT_MOTORS_READY);

    controller.begin();
    transmitCode(ACT_SERVOS_READY);

    ledSys.begin();
    
    // 5. Enable Watchdog
    WDT_timings_t config;
    config.timeout  = 5000;
    config.trigger  = 2500;
    config.callback = NULL;
    wdt.begin(config);

    transmitCode(SYS_BOOT_COMPLETE);
    lastCommandTime = millis(); 
}

// --- LOOP ---
void loop() {
    wdt.feed();
    unsigned long now = millis();

    // 1. READ INPUTS (USB & Radio)
    checkInput(Serial, usbBuffer, usbIndex);
    checkInput(APC220, radioBuffer, radioIndex);

    // 2. FAILSAFE CHECK
    if (!failsafeTriggered && (now - lastCommandTime > FAILSAFE_TIMEOUT)) {
        failsafeTriggered = true;
        leftMotor.emergencyStop();
        rightMotor.emergencyStop();
        controller.emergencyStop();
        
        isLeftMotorActive = false;
        isRightMotorActive = false;
        
        for(int i=0; i<6; i++) servoCommands[i] = 0;
        
        transmitCode(SAFE_FAILSAFE_TRIGGER);
    }

    // 3. UPDATE MOTORS
    if (now - lastMotorTime >= MOTOR_INTERVAL) {
        lastMotorTime = now;
        leftMotor.update();
        rightMotor.update();
    }

    // 4. UPDATE SERVOS
    if (now - lastServoTime >= SERVO_INTERVAL) {
        lastServoTime = now;
        controller.update(servoCommands);
    }

    // 5. UPDATE LEDs
    // Pass 'serialCommunicationFlag' to control Pin 24 blinking
    ledSys.update(isLeftMotorActive, isRightMotorActive, controller.isActive(), serialCommunicationFlag);
}