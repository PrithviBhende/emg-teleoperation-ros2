/* Due ONLY. Raw A0, 12 bits, timer-paced 2000 Hz, no digital filters.
   USE A REVIEWED ANALOGUE VOLTAGE ADAPTER: A0 MUST REMAIN WITHIN 0..3.3 V.
   No human-connected acquisition without a reviewed electrical safety arrangement.
   Default: Due NATIVE USB. Upload using either appropriate Due board/port setting.
   Set USE_NATIVE_USB to 0 to stream over the programming port at 115200 baud.
   This sketch is intentionally incompatible with the old version-4 packet format.
*/
#include <Arduino.h>
#if !defined(ARDUINO_ARCH_SAM)
#error "Select Arduino Due. This firmware is not for UNO or ESP32."
#endif
#define USE_NATIVE_USB 1
#if USE_NATIVE_USB
#define LINK SerialUSB
#else
#define LINK Serial
#endif
constexpr uint32_t FS = 2000, PERIOD_US = 500;
constexpr uint16_t RING = 2048, MASK = RING - 1;
struct Sample { uint32_t seq, tick; uint16_t value; };
volatile Sample ringBuffer[RING];
volatile uint16_t head = 0, tail = 0;
volatile uint32_t sequence = 0, overruns = 0, lateSamples = 0, previousTick = 0;
volatile bool streaming = false;

void TC3_Handler() {
  TC_GetStatus(TC1, 0);
  if (!streaming) return;
  uint32_t tick = micros();
  if (previousTick) {
    uint32_t elapsed = tick - previousTick;
    if (elapsed < 400 || elapsed > 600) lateSamples++;
  }
  previousTick = tick;
  uint16_t value = analogRead(A0); // conversion begins in periodic ISR, not USB loop
  uint32_t seq = sequence++;
  uint16_t next = (head + 1) & MASK;
  if (next == tail) { overruns++; return; }
  ringBuffer[head].seq = seq;
  ringBuffer[head].tick = tick;
  ringBuffer[head].value = value;
  __DMB();
  head = next;
}

void put16(uint8_t *p, uint16_t x) { p[0] = x; p[1] = x >> 8; }
void put32(uint8_t *p, uint32_t x) { for (int i=0; i<4; i++) p[i] = x >> (8*i); }
uint32_t crc32(const uint8_t *p, size_t n) {
  uint32_t crc = 0xffffffffUL;
  while (n--) {
    crc ^= *p++;
    for (int i=0; i<8; i++) crc = (crc >> 1) ^ (0xedb88320UL & (0UL - (crc & 1)));
  }
  return ~crc;
}

void setup() {
  LINK.begin(115200);
  analogReadResolution(12);
  analogRead(A0); // initialise ADC before enabling timer interrupt
  pmc_set_writeprotect(false);
  pmc_enable_periph_clk(ID_TC3);
  TC_Configure(TC1, 0, TC_CMR_TCCLKS_TIMER_CLOCK1 | TC_CMR_WAVE | TC_CMR_WAVSEL_UP_RC);
  TC_SetRC(TC1, 0, VARIANT_MCK / 2 / FS);
  TC1->TC_CHANNEL[0].TC_IER = TC_IER_CPCS;
  TC1->TC_CHANNEL[0].TC_IDR = ~TC_IER_CPCS;
  NVIC_SetPriority(TC3_IRQn, 3);
  NVIC_EnableIRQ(TC3_IRQn);
  TC_Start(TC1, 0);
}

void loop() {
  while (LINK.available()) {
    int c = LINK.read();
    if (c == 'S' && !streaming) {
      noInterrupts();
      head = tail = 0;
      previousTick = 0;
      streaming = true;
      interrupts();
    } else if (c == 'X') {
      noInterrupts(); streaming = false; head = tail = 0; interrupts();
    }
  }
  if (!streaming || ((head - tail) & MASK) < 32) return;
  Sample samples[32];
  uint16_t n = 0;
  while (n < 32 && tail != head) {
    uint16_t t = tail;
    uint32_t seq = ringBuffer[t].seq;
    if (n && seq != samples[n-1].seq + 1) break; // preserve gaps after ring overflow
    samples[n].seq = seq;
    samples[n].tick = ringBuffer[t].tick;
    samples[n].value = ringBuffer[t].value;
    n++;
    __DMB();
    tail = (t + 1) & MASK;
  }
  uint8_t packet[94]; // 26-byte header + 64 ADC bytes + CRC32
  memcpy(packet, "EMG1", 4);
  packet[4] = 1; packet[5] = 12;
  put16(packet+6, FS);
  put32(packet+8, samples[0].seq);
  put32(packet+12, samples[0].tick);
  put32(packet+16, overruns);
  put32(packet+20, lateSamples);
  put16(packet+24, n);
  for (uint16_t i=0; i<n; i++) put16(packet+26+2*i, samples[i].value);
  size_t length = 26 + 2*n;
  put32(packet+length, crc32(packet, length));
  // Any truncated transport is caught by CRC/sequence checks on the PC.
  LINK.write(packet, length+4);
}
