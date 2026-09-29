# Actividad 5 - Control de brazo robótico (URDF) con ESP32 y Python

Control en tiempo real de un brazo robótico con pinza, definido en un archivo URDF, a partir de sensores leídos por un ESP32. Los datos viajan por UART hasta un script en Python que mueve el robot en simulación con PyBullet.

## Video de demostración
[Ver video de demostración](https://drive.google.com/file/d/197bOcFmKQTlkMuXpWbRsJB0ShagPWOyS/view?usp=sharing)

## Archivos
| Archivo | Descripción |
|---|---|
| `brazo.urdf` | Modelo del robot (base, dos eslabones, base de la pinza y dos dedos). |
| `esp32_brazo.ino` | Firmware del ESP32: lee los sensores y envía los datos por UART. |
| `control_brazo.py` | Script en Python que recibe los datos y controla el brazo en PyBullet. |
| `imagenes/` | Foto del montaje y pantallazos de la práctica. |

## El robot (URDF)
| Articulación | Tipo | Rango | Función |
|---|---|---|---|
| `joint_1` | Rotacional (eje Z) | ±2.5 rad | Giro de la base |
| `joint_2` | Rotacional (eje Y) | ±2.0 rad | Elevación del segundo eslabón |
| `joint_gripper` | Prismática (eje Z) | 0 a 0.15 m | Extensión vertical de la pinza (se mantiene en 0) |
| `joint_dedo_izq` | Prismática (eje X) | 0 a 0.05 m | Dedo izquierdo de la pinza |
| `joint_dedo_der` | Prismática (eje X) | 0 a 0.05 m | Dedo derecho de la pinza |

## Hardware
- ESP32 (ESP-WROOM-32)
- 2 potenciómetros
- 1 módulo joystick analógico
- Protoboard y cables

| Sensor | Pin del ESP32 | Controla |
|---|---|---|
| Potenciómetro 1 | GPIO34 | `joint_1` |
| Potenciómetro 2 | GPIO35 | `joint_2` |
| Joystick, eje X (VRx) | GPIO32 | Apertura y cierre de la pinza |

- Potenciómetros: extremos a 3V3 y GND, cursor al pin ADC.
- Joystick: alimentación y GND del módulo, VRx al GPIO32 (VRy y SW sin usar).

### Montaje
![Montaje del circuito](montajebrazo.png)

## Funcionamiento
1. **Lectura en el ESP32.** Cada entrada se lee con el ADC de 12 bits (0-4095). Para reducir el ruido se promedian 8 muestras. Cada 20 ms (50 Hz) el ESP32 envía por UART, a 115200 baudios, una línea con el formato `t_ms,a1,a2,a3`.
2. **Recepción en Python.** El script abre el puerto serial, valida cada línea (descarta las incompletas o con errores) y extrae los tres valores.
3. **Brazo.** Los valores de los potenciómetros se convierten a la posición de `joint_1` y `joint_2` con una interpolación lineal entre los límites de cada articulación, que se leen directamente del URDF. Se aplica control de posición (`POSITION_CONTROL`).
4. **Pinza.** El joystick vuelve al centro por resorte, por lo que su eje X se usa como velocidad y no como posición. Al empujarlo hacia un lado la pinza se abre gradualmente, hacia el otro se cierra, y al soltarlo (zona muerta alrededor del centro) se mantiene donde está. Si el sentido queda invertido se usa la opción `--invertir-pinza`.
5. **Tiempo real.** El script imprime cada segundo los valores leídos, la apertura de la pinza y la tasa de actualización del lazo de control (Hz).

## Cómo ejecutarlo
### 1. Cargar el firmware
En Arduino IDE selecciona la placa **ESP32 Dev Module** y el puerto del ESP32, y sube `esp32_brazo.ino`. En el Monitor Serial (115200 baudios) se ven líneas del tipo `t_ms,a1,a2,a3`. Cierra el Monitor Serial antes de continuar.

### 2. Entorno de Python
```powershell
python -m venv venv
venv\Scripts\activate
pip install pybullet pyserial
```

### 3. Ejecutar
```powershell
python control_brazo.py --port COM5              # con el ESP32 conectado (cambiar COM5)
python control_brazo.py --port COM5 --invertir-pinza   # si la pinza queda al revés
python control_brazo.py --sim                    # sin hardware, con señales simuladas
```
`brazo.urdf` debe estar en la misma carpeta que el script. Para cerrar, `Ctrl + C` o cerrar la ventana de PyBullet.

## Pruebas realizadas
- **Articulaciones:** giro de `joint_1` y `joint_2` a lo largo de todo su rango con los potenciómetros.
- **Pinza:** apertura y cierre de los dedos con el joystick.
- **Comunicación en tiempo real:** el movimiento del brazo en la simulación sigue los movimientos de los sensores sin retraso apreciable, y la tasa de actualización se muestra en la terminal.

### Pantallazos
![Simulación del brazo en PyBullet](imagenes/simulacion.png)

![Salida en la terminal](imagenes/terminal.png)
