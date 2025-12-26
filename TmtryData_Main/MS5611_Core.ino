void MS5611_Init() {
    if (!ms5611.begin(HIGH_RES)) {
        // CODE: 005006
        transmitCode(ERR_MS5611_FAIL);
    } else {
        // CODE: 002002
        transmitCode(SENS_MS5611_OK);
    }
    delay(500);
    ms5611.enableKalmanFilter(0.5, 0.5, 0.138);
    referencePressure = ms5611.readPressure();
}

void MS5611_CORE() {
    uint32_t    rawTemperature      = ms5611.readRawTemperature();
    uint32_t    rawPressure         = ms5611.readRawPressure();
                realTemperature     = ms5611.readTemperature();
                realPressure        = ms5611.readPressure();
                absoluteAltitude    = ms5611.getAltitude(realPressure);
                relativeAltitude    = ms5611.getAltitude(realPressure, referencePressure);
                Altitude_Filtered   = ms5611.kalmanFilter(relativeAltitude);
  
}