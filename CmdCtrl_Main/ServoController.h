#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <Adafruit_PWMServoDriver.h>
#include <Arduino.h>

class ServoController {
public:
    Adafruit_PWMServoDriver pwm;
    static const int    numServos   = 6;
    int                 servoMin    = 150;
    int                 servoMax    = 600;
    float               angles[numServos];
    float               speeds[numServos];
    float               sensitivity[numServos];
    float               maxSpeed    = 2.0;
    float               accel       = 0.05;
    float               decel       = 0.05;

    ServoController() : pwm() {
        for (int i = 0; i < numServos; i++) {
            angles[i]       = 90;
            speeds[i]       = 0;
            sensitivity[i]  = 1.0;
        }
    }

    void begin() {
        pwm.begin();
        pwm.setPWMFreq(60);
        delay(10);
    }
    
    void emergencyStop() {
        for(int i = 0; i < numServos; i++) speeds[i] = 0;
    }

    bool isActive() {
        for(int i = 0; i < numServos; i++) {
            if(abs(speeds[i]) > 0.01) return true;
        }
        return false;
    }

    int angleToPulse(int angle) {
        return map(angle, 0, 180, servoMin, servoMax);
    }

    void update(char commands[]) {
        for (int i = 0; i < numServos; i++) {
            float targetSpeed = 0;
            if (commands[i] == 'L') targetSpeed = -maxSpeed * sensitivity[i];
            else if (commands[i] == 'R') targetSpeed = maxSpeed * sensitivity[i];

            // Ramp logic
            if (speeds[i] < targetSpeed) speeds[i] = min(speeds[i] + accel, targetSpeed);
            else if (speeds[i] > targetSpeed) speeds[i] = max(speeds[i] - decel, targetSpeed);
            
            angles[i] += speeds[i];
            angles[i] = constrain(angles[i], 0, 180);
            pwm.setPWM(i, 0, angleToPulse((int)angles[i]));
        }
    }
};

#endif