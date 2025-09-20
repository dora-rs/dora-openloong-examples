import json
from dora import Node

def main():
    node = Node()
    print("工作流编排节点启动")
    state = "WAIT_MOVE"
    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "chassis_status":
                status = event["value"]
                # 兼容 pyarrow.lib.UInt8Array、bytes、str
                if type(status).__name__ == "UInt8Array":
                    status = status.to_numpy().tobytes().decode("utf-8")
                elif hasattr(status, "tobytes"):
                    status = status.tobytes().decode("utf-8")
                elif isinstance(status, bytes):
                    status = status.decode("utf-8")
                elif isinstance(status, str):
                    pass
                else:
                    raise TypeError(f"未知类型: {type(status)}")
                status = json.loads(status)
                print(f"收到底盘状态: {status}")
                if status.get("action") == "MOVE_COMPLETE":
                    node.send_output("next_action", json.dumps({"action": "MOVE_COMPLETE"}).encode())
            elif event["id"] == "joint_status":
                status = event["value"]
                # 兼容 pyarrow.lib.UInt8Array、bytes、str
                if type(status).__name__ == "UInt8Array":
                    status = status.to_numpy().tobytes().decode("utf-8")
                elif hasattr(status, "tobytes"):
                    status = status.tobytes().decode("utf-8")
                elif isinstance(status, bytes):
                    status = status.decode("utf-8")
                elif isinstance(status, str):
                    pass
                else:
                    raise TypeError(f"未知类型: {type(status)}")
                status = json.loads(status)
                print(f"收到关节状态: {status}")
                if status.get("action") == "JOINT_CONTROL" and status.get("status") == "SUCCESS":
                    node.send_output("next_action", json.dumps({"action": "JOINT_CONTROL_COMPLETE"}).encode())
            elif event["id"] == "mani_status":
                status = event["value"]
                # 兼容 pyarrow.lib.UInt8Array、bytes、str
                if type(status).__name__ == "UInt8Array":
                    status = status.to_numpy().tobytes().decode("utf-8")
                elif hasattr(status, "tobytes"):
                    status = status.tobytes().decode("utf-8")
                elif isinstance(status, bytes):
                    status = status.decode("utf-8")
                elif isinstance(status, str):
                    pass
                else:
                    raise TypeError(f"未知类型: {type(status)}")
                status = json.loads(status)
                print(f"收到机械臂状态: {status}")
                if status.get("action") == "GRAB" and status.get("status") == "SUCCESS":
                    node.send_output("next_action", json.dumps({"action": "GRAB_COMPLETE"}).encode())
                elif status.get("action") == "RETURN" and status.get("status") == "SUCCESS":
                    node.send_output("next_action", json.dumps({"action": "RETURN_COMPLETE"}).encode())
                elif status.get("action") == "MANI_CONTROL" and status.get("status") == "SUCCESS":
                    node.send_output("next_action", json.dumps({"action": "MANI_CONTROL_COMPLETE"}).encode())

if __name__ == "__main__":
    main()