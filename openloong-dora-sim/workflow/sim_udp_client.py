import json
import socket
import struct
import threading
import time
from dora import Node


class SimUdpClient:
    def __init__(self, ip: str = "0.0.0.0", port: int = 8000, send_period_s: float = 0.5) -> None:
        self.ip = ip
        self.port = port
        self.send_period_s = send_period_s

        # UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Command buffer mirrors tools/py_ui.py layout
        self.cmd = bytearray([
            0x81, 0, 0, 0, 0x60, 0,
            0,
            0, 0, 0, 0,
            0, 0, 0, 0,
            0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            0x29, 0x5C, 0x0F, 0x3F, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0x9A, 0x99, 0x19, 0x3E,
            0, 13, 0,
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        ])

        # Velocities (interpreted as UI joystick values)
        self.linear_x = 0.0
        self.linear_y = 0.0
        self.yaw_rate = 0.0

        self._stop_event = threading.Event()
        self._sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self._sender_thread.start()

    def _update_velocity_bytes(self) -> None:
        # Match tools/py_ui.py mapping: vy -> [7:11], -wz -> [11:15], -vx -> [15:19], scaled*100
        self.cmd[7:11] = struct.pack('<f', self.linear_y * 100.0)
        self.cmd[11:15] = struct.pack('<f', -self.yaw_rate * 100.0)
        self.cmd[15:19] = struct.pack('<f', -self.linear_x * 100.0)

    def _set_key(self, key: int, clear_velocity: bool = False) -> None:
        if clear_velocity:
            self.linear_x = 0.0
            self.linear_y = 0.0
            self.yaw_rate = 0.0
            self._update_velocity_bytes()
        self.cmd[84] = key

    def _sender_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.socket.sendto(self.cmd, (self.ip, self.port))
            except Exception:
                # Best-effort; do not crash the loop
                pass
            time.sleep(self.send_period_s)

    def shutdown(self) -> None:
        self._stop_event.set()
        try:
            self._sender_thread.join(timeout=1.0)
        except Exception:
            pass


def _decode_event_value(value):
    # Accept pyarrow UInt8Array, numpy-like, bytes, or str
    tname = type(value).__name__
    if tname == "UInt8Array":
        return value.to_numpy().tobytes().decode("utf-8")
    if hasattr(value, "tobytes"):
        return value.tobytes().decode("utf-8")
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, str):
        return value
    raise TypeError(f"Unsupported value type: {type(value)}")


def main() -> None:
    node = Node()
    client = SimUdpClient()
    try:
        for event in node:
            if event["type"] != "INPUT":
                continue

            event_id = event["id"]
            raw_value = event["value"]
            try:
                value = json.loads(_decode_event_value(raw_value))
            except Exception:
                value = {}

            # Handle chassis MOVE command
            if event_id == "chassis_command":
                action = value.get("action")
                if action == "MOVE":
                    target = value.get("target", {})
                    client.linear_x = float(target.get("x", 0.0))
                    client.linear_y = float(target.get("y", 0.0))
                    client.yaw_rate = float(target.get("wz", 0.0))
                    client._update_velocity_bytes()
                    # Start key like UI: [6] start
                    client._set_key(6, clear_velocity=False)
                    node.send_output("chassis_status", json.dumps({"action": "MOVE_COMPLETE", "status": "SUCCESS"}).encode())

            # Handle joint control (simulate immediate success)
            elif event_id == "joint_command":
                action = value.get("action")
                if action == "JOINT_CONTROL":
                    # Mirror UI behavior by switching to jntSdk mode key [23]
                    client._set_key(23, clear_velocity=True)
                    node.send_output("joint_status", json.dumps({"action": "JOINT_CONTROL", "status": "SUCCESS"}).encode())

            # Handle manipulation commands (simulate via keys and statuses)
            elif event_id == "mani_command":
                action = value.get("action")
                if action == "GRAB":
                    # Use a generic mani action key; follow UI mani section (e.g., 116)
                    client._set_key(116, clear_velocity=True)
                    node.send_output("mani_status", json.dumps({"action": "GRAB", "status": "SUCCESS"}).encode())
                elif action == "RETURN":
                    # Return-home mapping; reuse a safe key (e.g., 112 idle before return)
                    client._set_key(112, clear_velocity=True)
                    node.send_output("mani_status", json.dumps({"action": "RETURN", "status": "SUCCESS"}).encode())
                elif action == "MANI_CONTROL":
                    client._set_key(116, clear_velocity=True)
                    node.send_output("mani_status", json.dumps({"action": "MANI_CONTROL", "status": "SUCCESS"}).encode())
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()


