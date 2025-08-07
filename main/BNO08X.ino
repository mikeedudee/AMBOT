void IMU_Init(void) {
    if (!bno08x.begin_I2C()) {
            Serial.println("ERROR: BNO08x not detected. Halt.");
            while (1) { delay(1000); }
        }

        if (!bno08x.enableReport(SH2_ROTATION_VECTOR, 50)) {
            Serial.println("ERROR: Cannot enable Rotation Vector.");
            while (1) { delay(1000); }
        }

}

void quaternionToEuler(float qr, float qi, float qj, float qk, euler_t* ypr, bool degrees = false) {
    float sqr = sq(qr);
    float sqi = sq(qi);
    float sqj = sq(qj);
    float sqk = sq(qk);

    ypr->yaw   = atan2(2.0 * (qi * qj + qk * qr), (sqi - sqj - sqk + sqr));
    ypr->pitch = asin(-2.0 * (qi * qk - qj * qr) / (sqi + sqj + sqk + sqr));
    ypr->roll  = atan2(2.0 * (qj * qk + qi * qr), (-sqi - sqj + sqk + sqr));

    if (degrees) {
        ypr->yaw   *= RAD_TO_DEG;
        ypr->pitch *= RAD_TO_DEG;
        ypr->roll  *= RAD_TO_DEG;

        // Compass convention: heading increases clockwise
        ypr->yaw = 360.0f - ypr->yaw;
        if (ypr->yaw >= 360.0f) ypr->yaw -= 360.0f;
        if (ypr->yaw < 0.0f)    ypr->yaw += 360.0f;
    }
}

void IMU_CORE() {
    if (bno08x.getSensorEvent(&sensorValue)) {
        if (sensorValue.sensorId == SH2_ROTATION_VECTOR) {
            float qw = sensorValue.un.rotationVector.real;
            float qx = sensorValue.un.rotationVector.i;
            float qy = sensorValue.un.rotationVector.j;
            float qz = sensorValue.un.rotationVector.k;

            quaternionToEuler(qw, qx, qy, qz, &ypr, true);

            Yaw_Output      = ypr.yaw;
            Pitch_Output    = ypr.pitch;
            Roll_Output     = ypr.roll;
            Heading_Compass = Yaw_Output;
            Heading_True    = Heading_Compass + DECLINATION;

            if (Heading_True >= 360.0f) Heading_True -= 360.0f;
            if (Heading_True < 0.0f)    Heading_True += 360.0f;
        }
    }

        // Serial.print(Yaw_Output, 2);
        // Serial.print(" ");
        // Serial.print(Pitch_Output, 2);
        // Serial.print(" ");
        // Serial.print(Roll_Output, 2);
        // Serial.print(" ");
        // Serial.print(Heading_True, 2);
        // Serial.println(" deg");

}