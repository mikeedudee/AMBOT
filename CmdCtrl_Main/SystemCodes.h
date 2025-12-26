#ifndef SYSTEMCODES_H
#define SYSTEMCODES_H

// DRIVER UNIT CODES (2000-series modified for Actuators)
enum SystemCode : uint16_t {
    SYS_BOOT_START          = 1000,
    SYS_BOOT_COMPLETE       = 1001,
    
    // --- ACTUATOR STATUS ---
    ACT_INIT_START          = 2000,
    ACT_MOTORS_READY        = 2001,
    ACT_SERVOS_READY        = 2002,
    
    // --- SAFETY EVENTS ---
    SAFE_FAILSAFE_TRIGGER   = 4005, // "I haven't heard from you! Stopping."
    SAFE_FAILSAFE_CLEAR     = 4006, // "Command received. Resuming."
    
    // --- ERRORS ---
    ERR_I2C_HANG            = 5005,
    ERR_WATCHDOG_RESET      = 5007
};

#endif