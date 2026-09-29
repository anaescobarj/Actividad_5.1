"""
Actividad 5 - Control en tiempo real del brazo (brazo.urdf) desde un ESP32 por UART.

Lee lineas "t_ms,a1,a2,a3" (ADC 0..4095) y las mapea a:
  a1 -> joint_1
  a2 -> joint_2
  a3 -> joint_gripper, joint_dedo_izq, joint_dedo_der  (apertura/cierre de la pinza)

Los limites de cada articulacion se leen del propio URDF.

Uso:
  pip install pybullet pyserial
  python control_brazo.py --port COM3            # Windows
  python control_brazo.py --port /dev/ttyUSB0    # Linux
  python control_brazo.py --sim                  # sin hardware (senales simuladas)
"""
import argparse
import math
import time

import pybullet as p
import pybullet_data

ADC_MAX = 4095.0
JOINT_ARM = ["joint_1", "joint_2"]
JOINT_GRIP = ["joint_gripper", "joint_dedo_izq", "joint_dedo_der"]


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urdf", default="brazo.urdf")
    ap.add_argument("--port", default="COM3")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--sim", action="store_true", help="simula el ESP32 (sin hardware)")
    return ap.parse_args()


def joint_table(robot):
    """nombre -> (indice, limite_inferior, limite_superior)"""
    tabla = {}
    for i in range(p.getNumJoints(robot)):
        info = p.getJointInfo(robot, i)
        nombre = info[1].decode()
        tabla[nombre] = (i, info[8], info[9])
    return tabla


def mapear(adc, lo, hi):
    frac = min(max(adc / ADC_MAX, 0.0), 1.0)
    return lo + frac * (hi - lo)


def leer_uart(ser):
    """Devuelve (t_ms, a1, a2, a3) o None si la linea es invalida."""
    linea = ser.readline().decode(errors="ignore").strip()
    partes = linea.split(",")
    if len(partes) != 4:
        return None
    try:
        return tuple(int(x) for x in partes)
    except ValueError:
        return None


def leer_sim():
    t = time.time()
    a1 = int((math.sin(t * 0.8) + 1) / 2 * ADC_MAX)
    a2 = int((math.sin(t * 0.5 + 1) + 1) / 2 * ADC_MAX)
    a3 = int((math.sin(t * 1.5) + 1) / 2 * ADC_MAX)
    time.sleep(0.02)
    return (int(t * 1000), a1, a2, a3)


def main():
    args = parse_args()

    ser = None
    if not args.sim:
        import serial
        ser = serial.Serial(args.port, args.baud, timeout=1)
        time.sleep(2)  # el ESP32 se reinicia al abrir el puerto
        ser.reset_input_buffer()

    p.connect(p.GUI)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.loadURDF("plane.urdf")
    robot = p.loadURDF(args.urdf, useFixedBase=True)
    joints = joint_table(robot)
    print("Articulaciones encontradas:", {k: (round(v[1], 3), round(v[2], 3)) for k, v in joints.items()})

    n, t0, t_print = 0, time.time(), time.time()
    try:
        while p.isConnected():
            datos = leer_sim() if args.sim else leer_uart(ser)
            if datos is None:
                continue
            _, a1, a2, a3 = datos

            for nombre, adc in zip(JOINT_ARM, (a1, a2)):
                idx, lo, hi = joints[nombre]
                p.setJointMotorControl2(robot, idx, p.POSITION_CONTROL,
                                        targetPosition=mapear(adc, lo, hi), force=50)
            for nombre in JOINT_GRIP:
                idx, lo, hi = joints[nombre]
                p.setJointMotorControl2(robot, idx, p.POSITION_CONTROL,
                                        targetPosition=mapear(a3, lo, hi), force=20)

            p.stepSimulation()
            n += 1
            if time.time() - t_print >= 1.0:  # validacion de tiempo real
                hz = n / (time.time() - t0)
                print(f"ADC=({a1:4d},{a2:4d},{a3:4d})  tasa de actualizacion: {hz:5.1f} Hz")
                t_print = time.time()
    except KeyboardInterrupt:
        pass
    finally:
        if ser:
            ser.close()
        if p.isConnected():
            p.disconnect()


if __name__ == "__main__":
    main()
