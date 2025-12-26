// U-BLOX CONFIGURATION STRINGS (Neo M10 / M8)
// UBX-CFG-PRT: Set Port 1 (UART) to 115200 Baud, 8N1
// Header: 0xB5, 0x62, Class: 0x06, ID: 0x00 ...
const byte setBaud115200[] = {
    0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00,
    0xD0, 0x08, 0x00, 0x00, 0x00, 0xC2, 0x01, 0x00, 0x07, 0x00,
    0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0xB0, 0x79
};

// UBX-CFG-RATE: Set Navigation/Measurement Rate to 10Hz (100ms)
const byte setRate10Hz[] = {
    0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, 0x64, 0x00, 0x01, 0x00, 
    0x01, 0x00, 0x7A, 0x12
};

void GPS_Init() {
    // 1. Start at default 9600 to establish contact
    GPSSerial.begin(9600);
    // CODE: 002004 (GPS OK)
    transmitCode(SENS_GPS_OK);
    delay(100);

    // 2. Send Command: "Switch to 115200 Baud"
    GPSSerial.write(setBaud115200, sizeof(setBaud115200));
    GPSSerial.flush(); // Wait for transmission to finish
    delay(100);        // Wait for GPS to process

    // 3. Restart Teensy Serial at the new high speed
    GPSSerial.end();
    // Now 115200 
    GPSSerial.begin(GPSBaud);
    delay(200);

    // 4. Send Command: "Set Update Rate to 10Hz"
    GPSSerial.write(setRate10Hz, sizeof(setRate10Hz));
    delay(100);

    // 5. Verify Fix
    unsigned long start = millis();
    // Wait up to 5 seconds for a fix
    while (millis() - start < 5000) { 
        while (GPSSerial.available()) {
            if (gps.encode(GPSSerial.read()) && gps.location.isValid()) {
                GPS_Latitude_Init  = gps.location.lat();
                GPS_Longitude_Init = gps.location.lng();
                return;
            }
        }
    }
}

void GPS_CORE() {
    // Process incoming at high speed
    while (GPSSerial.available() > 0) {
        if (gps.encode(GPSSerial.read())) {
            displayInfo();
        }
    }
    
    // Warning logic
    static bool gpsWarningShown = false;
    if (millis() > 5000 && gps.charsProcessed() < 10 && !gpsWarningShown) {
        gpsWarningShown = true; 
    }
}

void displayInfo() {
    // --- NEW: SPEED CALCULATION WITH FILTER ---
    if (gps.speed.isValid()) {
        GPS_Speed_Kmph = gps.speed.kmph();
        GPS_Speed_Mps  = gps.speed.mps();
        
        // Apply EMA Filter
        Filtered_GPS_Speed = (FILTER_ALPHA * GPS_Speed_Mps) + ((1.0f - FILTER_ALPHA) * Filtered_GPS_Speed);
        
    } else {
        GPS_Speed_Kmph = 0.0f;
        GPS_Speed_Mps  = 0.0f;
        // Optional: Decay the filtered speed to 0 if GPS is lost, rather than hard reset
        Filtered_GPS_Speed *= 0.95f; 
    }
}