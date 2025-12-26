#ifndef SDCARDLOGGER_H
#define SDCARDLOGGER_H

#include <SdFat.h>
#include "GlobalVariables.h"

class SDCardLogger {
    public:
        // Constructor
        SDCardLogger();

        /// Try to initialize the SD on SDIO.
        // Returns true if successful.
        bool begin();

        /// Append a C-string (char array) to the file.
        // Uses a buffer flush strategy for speed.
        void logValue(const char* value);

        /// Safely close the file (call before power down if possible).
        void end();

        /// Check if logger is healthy.
        bool isReady() const { return _ready; }

    private:
        static constexpr int                MAX_ATTEMPTS        = 1; // Fast fail to avoid boot loop
        static constexpr int                SYNC_INTERVAL       = 10; // Flush to disk every 10 writes
        static constexpr char               FILENAME[]          = "data.csv"; 

        SdFs   _sd;
        FsFile _file;
        bool   _ready;
        int    _syncCounter;
};

// Extern instance for global access if needed, 
// or instantiate in main.
extern SDCardLogger logger; 

#endif  // SDCARDLOGGER_H