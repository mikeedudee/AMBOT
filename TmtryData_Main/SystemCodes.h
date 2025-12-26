/*
Code Standard (Reference Table)
    1000 - 1999 : SYSTEM STATES — Boot Sequence, modes, operational status.
    2000 - 2999 : SENSORS — Initialization success, calibration events, fix acquired, etc.
    4000 - 4999 : ERRORS (Recoverable) — Sensor timeouts, temporary data loss, retries.
    5000 - 5999 : CRITICAL FAULTS — Hardware failure, e.g. SD Card dead, I2C Lockup, etc.
*/

#ifndef SYSTEMCODES_H
#define SYSTEMCODES_H

// USING UINT16_T (0 - 65535) for efficiency
enum SystemCode : uint16_t {

        // 1000 : SYSTEM STATE
        SYS_BOOT_START          = 1000,
        SYS_BOOT_COMPLETE       = 1001,
        SYS_READY_IDLE          = 1002,
        SYS_LOGGING_ACTIVE      = 1003,
        SYS_SHUTDOWN            = 1004,

        // 2000 : SENSORS INFO
        SENS_INIT_START         = 2000,
        SENS_SD_OK              = 2001,
        SENS_MS5611_OK          = 2002,
        SENS_IMU_OK             = 2003,
        SENS_GPS_OK             = 2004,
        SENS_GPS_3D_FIX         = 2005,
        SENS_CALIB_COMPLETE     = 2006,

        // 4000 : WARNINGS (Non-fatal erros)
        WARN_GPS_NO_FIX         = 4001,
        WARN_SD_SLOW            = 4004,

        // 5000 : CRITICAL ERROS
        ERR_SD_INIT_FAIL        = 5001,
        ERR_SD_WRITE_FAIL       = 5002,
        ERR_IMU_FAIL            = 5003,
        ERR_GPS_TIMEOUT         = 5004,
        ERR_I2C_BUS_HANG        = 5005,
        ERR_MS5611_FAIL         = 5006,
        ERR_WATCHDOG_RESET      = 5010,
        ERR_FREEZE_DETECTED     = 5011

};

#endif