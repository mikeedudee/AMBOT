#ifndef MOTOR_DRIVER_H
#define MOTOR_DRIVER_H

#include <Arduino.h>

class Motor {
private:
    int RPWM, LPWM, REN, LEN;
    int targetPWM, currentPWM;
    int pwmStep;

public:
    Motor(int rpwm, int lpwm, int ren, int len, int step = 5);
    void begin(int pwmFreqHz = 15000, int pwmResBits = 8);
    void setTarget(int pwm);      
    void update();                
    
    // Safety: Immediate Hard Stop
    void emergencyStop(); 
    
    int getCurrentPWM() const;
};

#endif