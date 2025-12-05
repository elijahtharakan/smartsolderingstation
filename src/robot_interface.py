"""Robot interface abstractions: Serial and Mock implementations."""
from typing import Optional

class RobotInterface:
    def send_command(self, cmd: str) -> None:
        """Send a plain-text command to the robot. Override in implementations."""
        raise NotImplementedError()


class MockRobot(RobotInterface):
    def __init__(self):
        self.sent = []

    def send_command(self, cmd: str) -> None:
        print(f"[MockRobot] send: {cmd}")
        self.sent.append(cmd)


class SerialRobot(RobotInterface):
    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 115200, timeout: float = 1.0):
        try:
            import serial
        except Exception:
            raise RuntimeError("pyserial not installed or unavailable")
        self.ser = serial.Serial(port, baudrate=baud, timeout=timeout)

    def send_command(self, cmd: str) -> None:
        if not self.ser or not self.ser.is_open:
            raise RuntimeError("serial port not open")
        # send with newline as delimiter
        raw = (cmd + "\n").encode("utf-8")
        self.ser.write(raw)


class PiGPIORobot(RobotInterface):
    """GPIO-based robot controller for Raspberry Pi.

    Supports simple commands encoded as strings:
    - `relay:<pin>:on` or `relay:<pin>:off`
    - `servo:<pin>:<value>` where <value> is -1.0..1.0 for gpiozero.Servo
    - `gpio:<pin>:on|off` general purpose

    This class uses `gpiozero` when available; falls back to RPi.GPIO if needed.
    """

    def __init__(self):
        # lazy import to avoid import errors on non-Pi systems
        try:
            from gpiozero import Servo, DigitalOutputDevice
            self._backend = 'gpiozero'
            self._Servo = Servo
            self._Digital = DigitalOutputDevice
            self._devices = {}
        except Exception:
            try:
                import RPi.GPIO as GPIO
                import time
                self._backend = 'RPi.GPIO'
                GPIO.setmode(GPIO.BCM)
                self._GPIO = GPIO
                self._pwm = {}
            except Exception:
                raise RuntimeError("No GPIO backend available (gpiozero or RPi.GPIO required on Raspberry Pi)")

    def _get_device(self, pin: int):
        if self._backend == 'gpiozero':
            if pin not in self._devices:
                # DigitalOutputDevice defaults to active_high True
                self._devices[pin] = self._Digital(pin)
            return self._devices[pin]
        return None

    def send_command(self, cmd: str) -> None:
        # parse simple commands
        try:
            parts = cmd.split(":")
            if parts[0] == 'relay' and len(parts) >= 3:
                pin = int(parts[1])
                state = parts[2].lower()
                if self._backend == 'gpiozero':
                    dev = self._get_device(pin)
                    if state in ('on', '1', 'true'):
                        dev.on()
                    else:
                        dev.off()
                else:
                    # RPi.GPIO fallback
                    if not hasattr(self._GPIO, 'pins_setup'):
                        self._GPIO.setup(pin, self._GPIO.OUT)
                    if state in ('on', '1', 'true'):
                        self._GPIO.output(pin, self._GPIO.HIGH)
                    else:
                        self._GPIO.output(pin, self._GPIO.LOW)
                return

            if parts[0] == 'servo' and len(parts) >= 3:
                pin = int(parts[1])
                val = float(parts[2])
                if self._backend == 'gpiozero':
                    # Servo expects value in -1..1
                    if pin not in self._devices:
                        self._devices[pin] = self._Servo(pin)
                    self._devices[pin].value = max(-1.0, min(1.0, val))
                else:
                    # RPi.GPIO PWM example: convert -1..1 to pwm duty cycle
                    duty = (val + 1.0) / 2.0 * 100.0
                    if pin not in self._pwm:
                        self._GPIO.setup(pin, self._GPIO.OUT)
                        p = self._GPIO.PWM(pin, 50)
                        p.start(duty)
                        self._pwm[pin] = p
                    else:
                        self._pwm[pin].ChangeDutyCycle(duty)
                return

            if parts[0] == 'gpio' and len(parts) >= 3:
                pin = int(parts[1])
                state = parts[2].lower()
                if self._backend == 'gpiozero':
                    dev = self._get_device(pin)
                    if state in ('on', '1', 'true'):
                        dev.on()
                    else:
                        dev.off()
                else:
                    self._GPIO.setup(pin, self._GPIO.OUT)
                    self._GPIO.output(pin, self._GPIO.HIGH if state in ('on', '1', 'true') else self._GPIO.LOW)
                return

            # unknown command: print/log
            print(f"[PiGPIORobot] Unknown command: {cmd}")
        except Exception as e:
            print(f"[PiGPIORobot] Error handling command '{cmd}': {e}")
