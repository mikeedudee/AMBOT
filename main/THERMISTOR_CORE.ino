void THERMISTOR_CORE() {
    int raw = analogRead(A0);
    constexpr float VREF = 5.0f;
    constexpr int MAX_RAW = (1 << 12) - 1;  // 4095 for 12-bit ADC

    if (raw <= 0 || raw >= MAX_RAW) {
        // Invalid ADC reading, set status to 0
        THERMISTOR_STATUS = 0;
        return;
    }

    float Vtherm = raw * (VREF / float(MAX_RAW));

    // Prevent division by zero if Vtherm approaches VREF
    if (VREF - Vtherm <= 0.0f) {
        THERMISTOR_STATUS = 0;
        return;
    }

    float Rfixed = THERMISTOR_R0;  // 10 kΩ reference resistor
    float Rtherm = Rfixed * Vtherm / (VREF - Vtherm);

    // Calculate inverse temperature (Kelvin)
    float invT = (1.0f / THERMISTOR_TEMP_INIT) + (log(Rtherm / THERMISTOR_R0) / THERMISTOR_BETA);

    // Convert to Celsius and apply calibration offset (-40)
    Temperature_Therm = (1.0f / invT - 273.15f) - 40.0f;

    THERMISTOR_STATUS = 1;  // Valid reading
}
