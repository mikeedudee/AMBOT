#include "SDCardLogger.h"

// Instantiate the global object
SDCardLogger logger;

SDCardLogger::SDCardLogger() : _ready(false), _syncCounter(0) {}

bool SDCardLogger::begin() {
    // If already ready, don't re-init
    if (_ready) return true;

    // Ensure any prior session is closed
    if (_sd.card()) _sd.end();

    // Initialize SD Card
    if (!_sd.begin(SdioConfig(FIFO_SDIO))) {
        SDCard_Status = 0; // Update Global Variable
        _ready = false;
        return false;
    }

    // Open File ONCE
    // O_APPEND: Add to end of file
    // O_CREAT: Create if doesn't exist
    // O_RDWR: Read/Write permission
    _file = _sd.open(FILENAME, O_RDWR | O_CREAT | O_APPEND);

    if (!_file) {
        SDCard_Status = 0;
        _ready = false;
        return false;
    }

    // Success
    SDCard_Status = 1;
    _ready = true;
    _syncCounter = 0;
    
    // Optional: Write a newline to separate flight sessions
    _file.println(F("--- NEW SESSION ---"));
    _file.sync();
    
    return true;
}

void SDCardLogger::logValue(const char* value) {
    // Safety check: Do not write if init failed
    if (!_ready || !_file) {
        // Optional: Try to recover? 
        // For strict safety, we usually just stop logging to prevent stalling.
        return;
    }

    _file.println(value);
    
    // Periodic Sync (Flush)
    // Ensures data is physically written to SD card periodically
    // without the massive overhead of close()/open()
    if (++_syncCounter >= SYNC_INTERVAL) {
        _file.sync();
        _syncCounter = 0;
    }
}

void SDCardLogger::end() {
    if (_file) {
        _file.sync();
        _file.close();
    }
    _ready = false;
    SDCard_Status = 0;
}