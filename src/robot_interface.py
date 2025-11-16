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
