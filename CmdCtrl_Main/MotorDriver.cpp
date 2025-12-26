#include "MotorDriver.h"

Motor::Motor(int rpwmPin, int lpwmPin, int renPin, int lenPin, int step)
    : RPWM(rpwmPin), LPWM(lpwmPin), REN(renPin), LEN(lenPin), pwmStep(step),
      targetPWM(0), currentPWM(0) {}

void Motor::begin(int pwmFreqHz, int pwmResBits) {
    pinMode(RPWM,   OUTPUT);
    pinMode(LPWM,   OUTPUT);
    pinMode(REN,    OUTPUT);
    pinMode(LEN,    OUTPUT);
    
    // Enable Pins (Teensy logic usually needs these HIGH)
    digitalWrite(REN, HIGH);
    digitalWrite(LEN, HIGH);
    
    analogWriteResolution(pwmResBits);
    analogWriteFrequency(RPWM, pwmFreqHz);
    analogWriteFrequency(LPWM, pwmFreqHz);
    
    emergencyStop(); // Start in safe mode
}

void Motor::setTarget(int pwm) {
    targetPWM = constrain(pwm, -255, 255);
}

void Motor::update() {
    // Ramp logic
    if(currentPWM < targetPWM) currentPWM = min(currentPWM + pwmStep, targetPWM);
    else if(currentPWM > targetPWM) currentPWM = max(currentPWM - pwmStep, targetPWM);

    if(currentPWM >= 0){
        analogWrite(RPWM, currentPWM);
        analogWrite(LPWM, 0);
    } else {
        analogWrite(RPWM, 0);
        analogWrite(LPWM, -currentPWM);
    }
}

// CRITICAL SAFETY FUNCTION
void Motor::emergencyStop() {
    targetPWM   = 0;
    currentPWM  = 0;
    analogWrite(RPWM, 0);
    analogWrite(LPWM, 0);
}

int Motor::getCurrentPWM() const { return currentPWM; }