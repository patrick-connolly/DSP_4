// Arduino Uno R3 board self-test
//
// Run with NOTHING wired to the header pins: the I/O test briefly drives every
// pin from D2 to A5 HIGH and LOW.
//
// Open the serial monitor at 115200 baud. The test runs once at boot. After that:
//   t  run the full self-test again
//   a  print live analog readings A0-A5
//   b  blink the built-in LED (D13)
//   h  help
// Any other key is echoed back, which confirms serial RX works.

#include <Arduino.h>
#include <EEPROM.h>

static const uint32_t BAUD = 115200;
static const uint8_t FIRST_TEST_PIN = 2;  // D0/D1 carry the USB serial link
static const uint8_t LAST_TEST_PIN = A5;  // D2..D13, then A0..A5 (pins 14..19)

static uint8_t passCount, warnCount, failCount;

enum Status { PASS, WARN, FAIL, INFO };

static void tag(Status s) {
  switch (s) {
    case PASS: Serial.print(F("[PASS] ")); passCount++; break;
    case WARN: Serial.print(F("[WARN] ")); warnCount++; break;
    case FAIL: Serial.print(F("[FAIL] ")); failCount++; break;
    case INFO: Serial.print(F("[INFO] ")); break;
  }
}

static void printPinName(uint8_t pin) {
  if (pin >= A0) {
    Serial.print('A');
    Serial.print(pin - A0);
  } else {
    Serial.print('D');
    Serial.print(pin);
  }
}

// --- Digital I/O --------------------------------------------------------------
// For each pin: drive HIGH and read back, drive LOW and read back, then enable the
// internal pull-up and check it reads HIGH. A pin stuck HIGH/LOW (damaged or
// shorted) fails the drive test; something wired to it usually trips the pull-up.
static void testDigitalPins() {
  uint8_t problems = 0;
  for (uint8_t pin = FIRST_TEST_PIN; pin <= LAST_TEST_PIN; pin++) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, HIGH);
    delayMicroseconds(50);
    bool high = digitalRead(pin) == HIGH;
    digitalWrite(pin, LOW);
    delayMicroseconds(50);
    bool low = digitalRead(pin) == LOW;

    pinMode(pin, INPUT_PULLUP);
    delayMicroseconds(500);
    bool pulledUp = digitalRead(pin) == HIGH;
    pinMode(pin, INPUT);

    if (!high || !low) {
      tag(FAIL);
      Serial.print(F("Digital I/O "));
      printPinName(pin);
      Serial.println(!high ? F(": driven HIGH but reads LOW") : F(": driven LOW but reads HIGH"));
      problems++;
    } else if (!pulledUp) {
      tag(WARN);
      Serial.print(F("Digital I/O "));
      printPinName(pin);
      Serial.println(F(": pull-up reads LOW (is something connected?)"));
      problems++;
    }
  }
  if (problems == 0) {
    tag(PASS);
    Serial.println(F("Digital I/O D2-D13, A0-A5: drive HIGH/LOW and pull-ups OK"));
  }
  pinMode(LED_BUILTIN, OUTPUT);
}

// --- ADC ----------------------------------------------------------------------
// Drive each analog pin HIGH then LOW and check the ADC sees ~1023 and ~0.
static void testAnalog() {
  analogReference(DEFAULT);
  for (uint8_t i = 0; i < 4; i++) analogRead(A0);  // let AREF settle after internal-ref reads
  delay(10);

  uint8_t problems = 0;
  for (uint8_t pin = A0; pin <= A5; pin++) {
    pinMode(pin, OUTPUT);
    digitalWrite(pin, HIGH);
    analogRead(pin);
    int high = analogRead(pin);
    digitalWrite(pin, LOW);
    analogRead(pin);
    int low = analogRead(pin);
    pinMode(pin, INPUT);

    if (high < 1000 || low > 20) {
      tag(FAIL);
      Serial.print(F("ADC "));
      printPinName(pin);
      Serial.print(F(": HIGH read "));
      Serial.print(high);
      Serial.print(F(", LOW read "));
      Serial.print(low);
      Serial.println(F(" (expected ~1023 / ~0)"));
      problems++;
    }
  }
  if (problems == 0) {
    tag(PASS);
    Serial.println(F("ADC A0-A5: reads ~1023 when HIGH, ~0 when LOW"));
  }
}

// Run one conversion on the current ADMUX setting, discarding the first result.
static uint16_t adcConvert() {
  for (uint8_t i = 0; i < 2; i++) {
    ADCSRA |= _BV(ADSC);
    while (bit_is_set(ADCSRA, ADSC)) {}
  }
  return ADC;
}

// --- Supply voltage -------------------------------------------------------------
// Measure the internal 1.1 V bandgap against AVcc to work out Vcc. The bandgap is
// only accurate to about 10%, so this is a sanity check, not a meter.
static void testSupplyVoltage() {
  ADMUX = _BV(REFS0) | _BV(MUX3) | _BV(MUX2) | _BV(MUX1);
  delay(2);
  uint16_t raw = adcConvert();
  long mv = raw ? 1125300L / raw : 0;  // 1.1 V * 1023 * 1000

  Status s = (mv >= 4300 && mv <= 5600) ? PASS : (mv >= 3000 && mv <= 6000) ? WARN : FAIL;
  tag(s);
  Serial.print(F("Supply voltage: "));
  Serial.print(mv / 1000);
  Serial.print('.');
  long frac = mv % 1000;
  if (frac < 100) Serial.print('0');
  if (frac < 10) Serial.print('0');
  Serial.print(frac);
  Serial.println(F(" V (expected ~5 V on USB)"));
}

// --- Internal temperature sensor --------------------------------------------------
// Uncalibrated, so it can be off by about 10 C. Shown for information only.
static void readChipTemperature() {
  ADMUX = _BV(REFS1) | _BV(REFS0) | _BV(MUX3);  // internal 1.1 V ref, channel 8
  delay(20);
  uint16_t raw = adcConvert();
  float celsius = (raw - 324.31f) / 1.22f;
  tag(INFO);
  Serial.print(F("Chip temperature: ~"));
  Serial.print(celsius, 0);
  Serial.println(F(" C (uncalibrated)"));
}

// --- EEPROM -------------------------------------------------------------------
// Write two patterns to the last byte, read them back, then restore the original.
static void testEeprom() {
  const int addr = E2END;
  const uint8_t patterns[] = {0xA5, 0x5A};
  uint8_t original = EEPROM.read(addr);
  bool ok = true;
  for (uint8_t p : patterns) {
    EEPROM.write(addr, p);
    if (EEPROM.read(addr) != p) ok = false;
  }
  EEPROM.write(addr, original);
  if (EEPROM.read(addr) != original) ok = false;

  tag(ok ? PASS : FAIL);
  Serial.print(F("EEPROM: write/read-back at address "));
  Serial.print(addr);
  Serial.println(ok ? F(" OK, original value restored") : F(" FAILED"));
}

// --- Timers -------------------------------------------------------------------
// The Arduino core starts Timer0 (millis) and Timers 1/2 (PWM). Check all three tick.
static void testTimers() {
  uint32_t m0 = millis();
  uint8_t t2a = TCNT2;
  uint16_t t1a = TCNT1;
  bool t1moved = false, t2moved = false;
  for (uint8_t i = 0; i < 5 && !(t1moved && t2moved); i++) {
    delayMicroseconds(37 + i * 11);
    if (TCNT1 != t1a) t1moved = true;
    if (TCNT2 != t2a) t2moved = true;
  }
  delay(20);
  bool t0moved = millis() != m0;

  bool ok = t0moved && t1moved && t2moved;
  tag(ok ? PASS : FAIL);
  Serial.print(F("Timers: T0 "));
  Serial.print(t0moved ? F("ok") : F("STOPPED"));
  Serial.print(F(", T1 "));
  Serial.print(t1moved ? F("ok") : F("STOPPED"));
  Serial.print(F(", T2 "));
  Serial.println(t2moved ? F("ok") : F("STOPPED"));
}

// --- SRAM ---------------------------------------------------------------------
extern int __heap_start, *__brkval;
static int freeRam() {
  int v;
  return (int)&v - (__brkval == 0 ? (int)&__heap_start : (int)__brkval);
}

static void blinkLed(uint8_t times) {
  pinMode(LED_BUILTIN, OUTPUT);
  for (uint8_t i = 0; i < times; i++) {
    digitalWrite(LED_BUILTIN, HIGH);
    delay(150);
    digitalWrite(LED_BUILTIN, LOW);
    delay(150);
  }
}

static void runAllTests() {
  passCount = warnCount = failCount = 0;
  Serial.println();
  Serial.println(F("===== Arduino Uno R3 self-test ====="));

  tag(PASS);
  Serial.println(F("Serial TX: you are reading this"));
  testDigitalPins();
  testAnalog();
  testSupplyVoltage();
  readChipTemperature();
  testEeprom();
  testTimers();

  tag(INFO);
  Serial.print(F("Free SRAM: "));
  Serial.print(freeRam());
  Serial.println(F(" of 2048 bytes"));

  tag(INFO);
  Serial.println(F("Built-in LED (D13) blinking 3 times: check it by eye"));
  blinkLed(3);

  Serial.print(F("===== Result: "));
  Serial.print(passCount);
  Serial.print(F(" passed, "));
  Serial.print(warnCount);
  Serial.print(F(" warnings, "));
  Serial.print(failCount);
  Serial.println(failCount ? F(" FAILED =====") : F(" failed: board OK ====="));
  Serial.println(F("Press 'h' for commands."));
}

static void printHelp() {
  Serial.println(F("Commands: t = run self-test, a = analog readings, b = blink LED, h = help"));
  Serial.println(F("Any other key is echoed back (serial RX test)."));
}

static void printAnalogReadings() {
  analogReference(DEFAULT);
  for (uint8_t i = 0; i < 4; i++) analogRead(A0);
  delay(10);
  for (uint8_t pin = A0; pin <= A5; pin++) {
    pinMode(pin, INPUT);
    analogRead(pin);
    int raw = analogRead(pin);
    printPinName(pin);
    Serial.print(F(": "));
    Serial.print(raw);
    Serial.print(F(" ("));
    Serial.print(raw * 5.0f / 1023.0f, 2);
    Serial.print(F(" V)"));
    Serial.print(pin < A5 ? F("  ") : F("\n"));
  }
  Serial.println(F("(Unconnected pins float, so random values on them are normal.)"));
}

void setup() {
  Serial.begin(BAUD);
  pinMode(LED_BUILTIN, OUTPUT);
  delay(500);
  runAllTests();
}

void loop() {
  // Slow heartbeat on D13 while idle, so you can see the sketch is running.
  static uint32_t lastToggle = 0;
  if (millis() - lastToggle >= 1000) {
    lastToggle = millis();
    digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
  }

  if (!Serial.available()) return;
  char c = Serial.read();
  switch (c) {
    case 't': case 'T': runAllTests(); break;
    case 'a': case 'A': printAnalogReadings(); break;
    case 'b': case 'B':
      Serial.println(F("Blinking LED 5 times"));
      blinkLed(5);
      break;
    case 'h': case 'H': case '?': printHelp(); break;
    case '\r': case '\n': break;
    default:
      Serial.print(F("Received '"));
      Serial.print(c);
      Serial.println(F("': serial RX works. Press 'h' for help."));
  }
}
