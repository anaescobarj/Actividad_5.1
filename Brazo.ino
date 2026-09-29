// Actividad 5 - Brazo robotico con pinza (URDF) controlado desde ESP32
// El ESP32 lee 2 potenciometros y un joystick y envia por UART lineas CSV: t_ms,a1,a2,a3
//   POT1 (GPIO34)        -> joint_1
//   POT2 (GPIO35)        -> joint_2
//   JOYSTICK VRx (GPIO32) -> pinza (joint_gripper + dedos)

const int PIN_POT1 = 34;
const int PIN_POT2 = 35;
const int PIN_POT3 = 32;

const unsigned long BAUD = 115200;
const unsigned long PERIODO_MS = 20;   // 50 Hz
const int N_MUESTRAS = 8;              // promedio simple para reducir ruido

unsigned long ultimo = 0;

int leerFiltrado(int pin) {
  long suma = 0;
  for (int i = 0; i < N_MUESTRAS; i++) suma += analogRead(pin);
  return suma / N_MUESTRAS;
}

void setup() {
  Serial.begin(BAUD);
  analogReadResolution(12);            // 0..4095
  analogSetAttenuation(ADC_11db);      // rango ~0-3.3 V
  pinMode(PIN_POT1, INPUT);
  pinMode(PIN_POT2, INPUT);
  pinMode(PIN_POT3, INPUT);
}

void loop() {
  unsigned long ahora = millis();
  if (ahora - ultimo >= PERIODO_MS) {
    ultimo = ahora;
    int a1 = leerFiltrado(PIN_POT1);
    int a2 = leerFiltrado(PIN_POT2);
    int a3 = leerFiltrado(PIN_POT3);
    Serial.printf("%lu,%d,%d,%d\n", ahora, a1, a2, a3);
  }
}