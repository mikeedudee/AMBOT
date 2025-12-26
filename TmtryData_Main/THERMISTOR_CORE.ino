void THERMISTOR_CORE() {
    int raw = analogRead(A0);
    
    // NOTE: Teensy 4.1 ADC is usually 3.3V. If using 3.3V power, change this to 3.3f.
    // If kept at 5.0f with 3.3V power, the reading will be skewed (likely the cause of the -25 error).
    constexpr float VREF = 5.0f; 
    constexpr int MAX_RAW = (1 << 12) - 1; // 4095
    
    // User defined calibration to match other sensors
    constexpr float CALIBRATION_OFFSET = 30.0f; 

    // Voltage calculation
    float Vtherm = raw * (VREF / float(MAX_RAW));
    
    // Safety: Prevent divide by zero if Vtherm approaches VREF
    if (Vtherm >= VREF) Vtherm = VREF - 0.001f;
    
    float Rfixed = THERMISTOR_R0; // 10 kΩ
    float Rtherm = Rfixed * Vtherm / (VREF - Vtherm);
    
    // Steinhart-Hart Beta equation
    float invT = (1.0f / THERMISTOR_TEMP_INIT) + (log(Rtherm / THERMISTOR_R0) / THERMISTOR_BETA);
    
    // Kelvin to Celsius + Calibration
    Temperature_Therm = ((1.0f / invT) - 273.15f) + CALIBRATION_OFFSET;
}