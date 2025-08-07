void MS5611_Init() {
    if (!ms5611.begin(HIGH_RES)) {
        MS5611_STATUS = 0;
        return;
    }
    MS5611_STATUS = 1;  // Sensor initialized successfully
    delay(500);
    ms5611.enableKalmanFilter(0.5, 0.5, 0.138);
    referencePressure = ms5611.readPressure();
}

void MS5611_CORE() {
    if (!MS5611_STATUS) {
        // Sensor not initialized or failed; skip reading
        return;
    }

    uint32_t rawTemperature = ms5611.readRawTemperature();
    uint32_t rawPressure    = ms5611.readRawPressure();
    
    realTemperature         = ms5611.readTemperature();
    realPressure            = ms5611.readPressure();

    if (realTemperature == 0.0f || realPressure == 0.0f) {
        MS5611_STATUS = 0;  // Invalid reading detected, mark sensor as offline
        return;
    } else {
        MS5611_STATUS = 1;  // Valid reading
    }

    absoluteAltitude    = ms5611.getAltitude(realPressure);
    relativeAltitude    = ms5611.getAltitude(realPressure, referencePressure);
    Altitude_Filtered   = ms5611.kalmanFilter(relativeAltitude);
}
