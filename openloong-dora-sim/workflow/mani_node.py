import json
import os
import sys
import time
import numpy as np
from dora import Node

# SDK path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "loong_sim_sdk_release"))
from sdk.loong_mani_sdk.loong_mani_sdk_udp import maniSdkCtrlDataClass, maniSdkClass


class MinimalManiNode:
    def __init__(self, ip: str = "0.0.0.0", port: int = 8003) -> None:
        # Degrees of freedom configuration
        self.jntNum = 19
        self.armDof = 7
        self.fingerDofLeft = 6
        self.fingerDofRight = 6
        self.neckDof = 2
        self.lumbarDof = 3

        # SDK
        self.ctrl = maniSdkCtrlDataClass(self.armDof, self.fingerDofLeft, self.fingerDofRight, self.neckDof, self.lumbarDof)
        self.sdk = maniSdkClass(ip, port, self.jntNum, self.fingerDofLeft, self.fingerDofRight)

        # Default modes similar to test_.py
        self.ctrl.inCharge = 1
        self.ctrl.filtLevel = 1
        self.ctrl.armMode = 4
        self.ctrl.fingerMode = 3
        self.ctrl.neckMode = 5
        self.ctrl.lumbarMode = 0

        # Default arm pose
        self.ctrl.armCmd = np.array([
            [0.4, 0.4, 0.1, 0, 0, 0, 0.5],
            [0.2, -0.4, 0.1, 0, 0, 0, 0.5]
        ], np.float32)

        self.ctrl.armFM = np.zeros((2, 6), np.float32)
        self.ctrl.fingerLeft = np.zeros(self.fingerDofLeft, np.float32)
        self.ctrl.fingerRight = np.zeros(self.fingerDofRight, np.float32)
        self.ctrl.neckCmd = np.zeros(self.neckDof, np.float32)
        self.ctrl.lumbarCmd = np.zeros(self.lumbarDof, np.float32)

    def send_once(self):
        # Non-blocking send/recv (best-effort)
        self.sdk.send(self.ctrl)
        self.sdk.recv()

    def handle_grab(self):
        # Simple grasp: move to mid pose and close fingers
        self.ctrl.armCmd[0] = np.array([0.3, 0.2, 0.0, 0, 0, 0, 0.5], np.float32)
        self.ctrl.armCmd[1] = np.array([0.3, -0.2, 0.0, 0, 0, 0, 0.5], np.float32)
        self.ctrl.fingerLeft[:] = 50
        self.ctrl.fingerRight[:] = 50
        for _ in range(20):  # ~0.4s
            self.send_once()
            time.sleep(0.02)

    def handle_return(self):
        # Return to default
        self.ctrl.armCmd[0] = np.array([0.4, 0.4, 0.1, 0, 0, 0, 0.5], np.float32)
        self.ctrl.armCmd[1] = np.array([0.2, -0.4, 0.1, 0, 0, 0, 0.5], np.float32)
        self.ctrl.fingerLeft[:] = 0
        self.ctrl.fingerRight[:] = 0
        for _ in range(20):
            self.send_once()
            time.sleep(0.02)

    def handle_custom(self, target: dict):
        if "left_arm" in target:
            self.ctrl.armCmd[0] = np.array(target["left_arm"], np.float32)
        if "right_arm" in target:
            self.ctrl.armCmd[1] = np.array(target["right_arm"], np.float32)
        if "left_fingers" in target:
            lf = np.array(target["left_fingers"], np.float32)
            self.ctrl.fingerLeft[:len(lf)] = lf
        if "right_fingers" in target:
            rf = np.array(target["right_fingers"], np.float32)
            self.ctrl.fingerRight[:len(rf)] = rf
        for _ in range(10):
            self.send_once()
            time.sleep(0.02)


def main():
    node = Node()
    mani = MinimalManiNode()
    print("最简 mani 节点已启动")
    for event in node:
        if event["type"] != "INPUT":
            continue
        event_id = event["id"]
        raw_value = event["value"]
        if event_id != "mani_command":
            continue
        try:
            if type(raw_value).__name__ == "UInt8Array":
                value = raw_value.to_numpy().tobytes().decode("utf-8")
            elif hasattr(raw_value, "tobytes"):
                value = raw_value.tobytes().decode("utf-8")
            elif isinstance(raw_value, bytes):
                value = raw_value.decode("utf-8")
            elif isinstance(raw_value, str):
                value = raw_value
            else:
                raise TypeError(f"Unsupported type: {type(raw_value)}")
            cmd = json.loads(value)
        except Exception:
            cmd = {}

        action = cmd.get("action")
        if action == "GRAB":
            mani.handle_grab()
            node.send_output("mani_status", json.dumps({"action":"GRAB","status":"SUCCESS"}).encode())
        elif action == "RETURN":
            mani.handle_return()
            node.send_output("mani_status", json.dumps({"action":"RETURN","status":"SUCCESS"}).encode())
        elif action == "MANI_CONTROL":
            mani.handle_custom(cmd.get("target", {}))
            node.send_output("mani_status", json.dumps({"action":"MANI_CONTROL","status":"SUCCESS"}).encode())


if __name__ == "__main__":
    main()
