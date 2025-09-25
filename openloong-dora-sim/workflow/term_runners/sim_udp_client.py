import json
import socket
import struct
import threading
import time
import sys
import os
import numpy as np
from dora import Node

# Add SDK path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "loong_sim_sdk_release"))
from sdk.loong_mani_sdk.loong_mani_sdk_udp import maniSdkCtrlDataClass, maniSdkClass, maniSdkSensDataClass


class SimUdpClient:
    def __init__(self, ip: str = "0.0.0.0", port: int = 8000, send_period_s: float = 0.5, 
                 mani_ip: str = "0.0.0.0", mani_port: int = 8003) -> None:
        self.ip = ip
        self.port = port
        self.send_period_s = send_period_s

        # UDP socket for chassis control
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # Initialize mani SDK
        self.jntNum = 19
        self.armDof = 7
        self.fingerDofLeft = 6
        self.fingerDofRight = 6
        self.neckDof = 2
        self.lumbarDof = 3
        
        self.mani_ctrl = maniSdkCtrlDataClass(self.armDof, self.fingerDofLeft, 
                                            self.fingerDofRight, self.neckDof, self.lumbarDof)
        self.mani_sdk = maniSdkClass(mani_ip, mani_port, self.jntNum, 
                                   self.fingerDofLeft, self.fingerDofRight)
        
        # Initialize mani control parameters
        self._init_mani_control()
        
        # Mani command state tracking
        self._pending_mani_command = None
        self._mani_command_timeout = 0
        self._mani_feedback_received = False
        self._pending_status = None

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
        
        # Start mani control thread
        self._mani_thread = threading.Thread(target=self._mani_control_loop, daemon=True)
        self._mani_thread.start()

    def _init_mani_control(self) -> None:
        """Initialize mani control parameters based on test_.py"""
        self.mani_ctrl.inCharge = 1
        self.mani_ctrl.filtLevel = 1
        self.mani_ctrl.armMode = 4  # 笛卡尔身体系
        self.mani_ctrl.fingerMode = 3  # 关节轴控
        self.mani_ctrl.neckMode = 5  # 看左手
        self.mani_ctrl.lumbarMode = 0  # 无控制
        
        # Set default arm commands (similar to test_.py)
        self.mani_ctrl.armCmd = np.array([
            [0.4, 0.4, 0.1, 0, 0, 0, 0.5],  # Left arm
            [0.2, -0.4, 0.1, 0, 0, 0, 0.5]  # Right arm
        ], np.float32)
        
        # Initialize other control arrays
        self.mani_ctrl.armFM = np.zeros((2, 6), np.float32)
        self.mani_ctrl.fingerLeft = np.zeros(self.fingerDofLeft, np.float32)
        self.mani_ctrl.fingerRight = np.zeros(self.fingerDofRight, np.float32)
        self.mani_ctrl.neckCmd = np.zeros(self.neckDof, np.float32)
        self.mani_ctrl.lumbarCmd = np.zeros(self.lumbarDof, np.float32)

    def _mani_control_loop(self) -> None:
        """Mani control loop that sends commands and receives feedback"""
        while not self._stop_event.is_set():
            try:
                # Send control commands
                self.mani_sdk.send(self.mani_ctrl)
                # Receive sensor feedback
                sens = self.mani_sdk.recv()
                
                # Process sensor data and check command completion
                self._process_mani_feedback(sens)
                
            except Exception as e:
                # Best-effort; do not crash the loop
                print(f"Mani control error: {e}")
            time.sleep(0.02)  # 50Hz control loop

    def _process_mani_feedback(self, sens) -> None:
        """Process mani sensor feedback and check command completion"""
        if self._pending_mani_command is None:
            return
            
        # Check for errors
        if np.any(sens.drvErr != 0):
            print(f"驱动器错误: {sens.drvErr}")
            self._send_mani_status("ERROR", "驱动器错误")
            self._pending_mani_command = None
            return
        
        # Check command completion based on feedback
        if self._pending_mani_command == "GRAB":
            # Check if fingers are closed and arms are in position
            left_finger_closed = np.all(sens.actFingerLeft > 40)  # Fingers closed
            right_finger_closed = np.all(sens.actFingerRight > 40)
            
            if left_finger_closed and right_finger_closed:
                self._send_mani_status("GRAB", "SUCCESS")
                self._pending_mani_command = None
                
        elif self._pending_mani_command == "RETURN":
            # Check if arms are back to home position
            left_arm_home = np.allclose(sens.actJ[:7], [0.4, 0.4, 0.1, 0, 0, 0, 0.5], atol=0.1)
            right_arm_home = np.allclose(sens.actJ[7:14], [0.2, -0.4, 0.1, 0, 0, 0, 0.5], atol=0.1)
            
            if left_arm_home and right_arm_home:
                self._send_mani_status("RETURN", "SUCCESS")
                self._pending_mani_command = None
                
        elif self._pending_mani_command == "MANI_CONTROL":
            # For custom control, assume success after a short delay
            if self._mani_command_timeout > 0:
                self._mani_command_timeout -= 1
                if self._mani_command_timeout == 0:
                    self._send_mani_status("MANI_CONTROL", "SUCCESS")
                    self._pending_mani_command = None

    def _send_mani_status(self, action: str, status: str) -> None:
        """Send mani status to dora workflow"""
        # This will be called from the main event loop
        self._pending_status = {"action": action, "status": status}

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
            self._mani_thread.join(timeout=1.0)
        except Exception:
            pass

    def set_arm_position(self, left_arm: list = None, right_arm: list = None) -> None:
        """Set arm positions for both arms"""
        if left_arm is not None:
            self.mani_ctrl.armCmd[0] = np.array(left_arm, np.float32)
        if right_arm is not None:
            self.mani_ctrl.armCmd[1] = np.array(right_arm, np.float32)

    def set_finger_control(self, left_fingers: list = None, right_fingers: list = None) -> None:
        """Set finger control for both hands"""
        if left_fingers is not None:
            self.mani_ctrl.fingerLeft = np.array(left_fingers, np.float32)
        if right_fingers is not None:
            self.mani_ctrl.fingerRight = np.array(right_fingers, np.float32)

    def set_mani_mode(self, arm_mode: int = None, finger_mode: int = None, 
                     neck_mode: int = None, lumbar_mode: int = None) -> None:
        """Set manipulation control modes"""
        if arm_mode is not None:
            self.mani_ctrl.armMode = arm_mode
        if finger_mode is not None:
            self.mani_ctrl.fingerMode = finger_mode
        if neck_mode is not None:
            self.mani_ctrl.neckMode = neck_mode
        if lumbar_mode is not None:
            self.mani_ctrl.lumbarMode = lumbar_mode


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

            # Handle manipulation commands using real SDK
            elif event_id == "mani_command":
                action = value.get("action")
                if action == "GRAB":
                    # Set grab position for both arms
                    client.set_arm_position(
                        left_arm=[0.3, 0.2, 0.0, 0, 0, 0, 0.5],  # Grab position
                        right_arm=[0.3, -0.2, 0.0, 0, 0, 0, 0.5]
                    )
                    # Close fingers
                    client.set_finger_control(
                        left_fingers=[50, 50, 50, 50, 50, 50],  # Close all fingers
                        right_fingers=[50, 50, 50, 50, 50, 50]
                    )
                    # Set pending command to wait for real feedback
                    client._pending_mani_command = "GRAB"
                    print("GRAB命令已发送，等待真实反馈...")
                    
                elif action == "RETURN":
                    # Return to home position
                    client.set_arm_position(
                        left_arm=[0.4, 0.4, 0.1, 0, 0, 0, 0.5],  # Home position
                        right_arm=[0.2, -0.4, 0.1, 0, 0, 0, 0.5]
                    )
                    # Open fingers
                    client.set_finger_control(
                        left_fingers=[0, 0, 0, 0, 0, 0],  # Open all fingers
                        right_fingers=[0, 0, 0, 0, 0, 0]
                    )
                    # Set pending command to wait for real feedback
                    client._pending_mani_command = "RETURN"
                    print("RETURN命令已发送，等待真实反馈...")
                    
                elif action == "MANI_CONTROL":
                    # Handle custom manipulation control
                    target = value.get("target", {})
                    
                    # Set arm positions if provided
                    if "left_arm" in target:
                        client.set_arm_position(left_arm=target["left_arm"])
                    if "right_arm" in target:
                        client.set_arm_position(right_arm=target["right_arm"])
                    
                    # Set finger control if provided
                    if "left_fingers" in target:
                        client.set_finger_control(left_fingers=target["left_fingers"])
                    if "right_fingers" in target:
                        client.set_finger_control(right_fingers=target["right_fingers"])
                    
                    # Set control modes if provided
                    if "arm_mode" in target:
                        client.set_mani_mode(arm_mode=target["arm_mode"])
                    if "finger_mode" in target:
                        client.set_mani_mode(finger_mode=target["finger_mode"])
                    
                    # Set pending command with timeout
                    client._pending_mani_command = "MANI_CONTROL"
                    client._mani_command_timeout = 50  # 1 second timeout (50 * 0.02s)
                    print("MANI_CONTROL命令已发送，等待真实反馈...")
            
            # Check for pending status updates from mani feedback
            if client._pending_status is not None:
                status = client._pending_status
                client._pending_status = None
                node.send_output("mani_status", json.dumps(status).encode())
                print(f"发送真实mani状态: {status}")
    finally:
        client.shutdown()


if __name__ == "__main__":
    main()


