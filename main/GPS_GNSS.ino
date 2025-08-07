void GPS_INIT() {
    if (!GPS_Serial) {
        GPS_STATUS = 0;
        return;
    }
    GPS_Serial.begin(GPSBaud);
    GPS_STATUS = 0;  // Initially no data yet
}

void GPS_CORE() {
    while (GPS_Serial.available() > 0) {
        char c = GPS_Serial.read();
        gps.encode(c);
    }

    if (gps.location.isUpdated()) {
        GPS_STATUS = 1;  // Valid update received

        // TIME
        if (gps.time.isValid()) {
            TIME_HOUR   = gps.time.hour();
            TIME_MINUTE = gps.time.minute();
            TIME_SECOND = gps.time.second();
        } else {
            TIME_HOUR   = 0.0f;
            TIME_MINUTE = 0.0f;
            TIME_SECOND = 0.0f;
        }

        // LATITUDE
        LATITUDE = gps.location.lat();

        // LONGITUDE
        LONGITUDE = gps.location.lng();

        // ALTITUDE
        if (gps.altitude.isValid()) {
            ALTITUDE = gps.altitude.meters();
        } else {
            ALTITUDE = 0.0f;
        }

        // Optional: Output can be done outside or controlled by caller
        // Serial.println("---------------------");
    } else {
        GPS_STATUS = 0;  // No valid update yet
    }
}
