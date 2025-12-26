// Existing double overload
void print_data(double data, int decimal) {
    Serial.println(data, decimal);
    APC220.println(data, decimal);
}

// New overload for C-strings (null-terminated char arrays)
void print_data(const char *s) {
    Serial.println(s);
    APC220.println(s);
}

// New overload for a single character
void print_data(char c) {
    Serial.println(c);
    APC220.println(c);
}

// NOTE: String object overload removed to enforce JSF Rule 3 (No Dynamic Memory)