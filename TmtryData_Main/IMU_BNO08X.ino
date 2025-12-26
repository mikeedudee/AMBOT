void IMU_Init(void) {
    if (!bno08x.begin_I2C()) {
      // CODE: 005003
      transmitCode(ERR_IMU_FAIL);
    } else {
      // CODE: 002003
      transmitCode(SENS_IMU_OK);
    }
    setReports(reportType, reportIntervalUs);
    
    // NEW: Enable Linear Acceleration for Velocity Calc (5000us = 200Hz)
    bno08x.enableReport(SH2_LINEAR_ACCELERATION, 5000); 

    delay(100);
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
    }
}

void quaternionToEulerRV(sh2_RotationVectorWAcc_t* rotational_vector, euler_t* ypr, bool degrees = false) {
    quaternionToEuler(rotational_vector->real, rotational_vector->i, rotational_vector->j, rotational_vector->k, ypr, degrees);
}

void quaternionToEulerGI(sh2_GyroIntegratedRV_t* rotational_vector, euler_t* ypr, bool degrees = false) {
    quaternionToEuler(rotational_vector->real, rotational_vector->i, rotational_vector->j, rotational_vector->k, ypr, degrees);
}

void IMU_CORE() {
  if (bno08x.wasReset()) {
    setReports(reportType, reportIntervalUs);
    bno08x.enableReport(SH2_LINEAR_ACCELERATION, 5000);
  }
  
  if (bno08x.getSensorEvent(&sensorValue)) {
    switch (sensorValue.sensorId) {
      case SH2_ARVR_STABILIZED_RV:
        quaternionToEulerRV(&sensorValue.un.arvrStabilizedRV, &ypr, true);
        break;
      case SH2_GYRO_INTEGRATED_RV:
        quaternionToEulerGI(&sensorValue.un.gyroIntegratedRV, &ypr, true);
        break;
        
      // --- NEW: LINEAR ACCELERATION FOR VELOCITY ---
     case SH2_LINEAR_ACCELERATION:
        IMU_Accel_X = sensorValue.un.linearAcceleration.x;
        IMU_Accel_Y = sensorValue.un.linearAcceleration.y;
        
        // --- APPLY EMA FILTER ---
        // Formula: New = (Alpha * Raw) + ((1-Alpha) * Old)
        Filtered_Accel_X = (FILTER_ALPHA * IMU_Accel_X) + ((1.0f - FILTER_ALPHA) * Filtered_Accel_X);
        
        // Integration: V = V0 + a*dt
        static unsigned long prevAccelTime  = 0;
        unsigned long currentAccelTime      = micros();
        
        if (prevAccelTime > 0) {
            float dt = (currentAccelTime - prevAccelTime) / 1000000.0f; // us to seconds
            
            // Use the FILTERED acceleration for integration
            // Deadband: Ignore tiny movements < 0.1 m/s^2
            if (abs(Filtered_Accel_X) > 0.1f) {
                IMU_Speed_X += Filtered_Accel_X * dt;
            } else {
                 // Friction decay: Slowly zero out speed if no acceleration
                 IMU_Speed_X *= 0.98f; 
            }
        }
        prevAccelTime = currentAccelTime;
        break;
    }

    Yaw_Output        = ypr.yaw;
    Pitch_Output      = ypr.pitch;
    Roll_Output       = ypr.roll;
    sensorStatusValue = sensorValue.status;
  }
}