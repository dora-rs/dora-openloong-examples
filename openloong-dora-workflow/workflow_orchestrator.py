import json
from dora import Node

def main():
    node = Node()
    print("🧩 工作流编排节点启动")
    state = "WAIT_MOVE"
    for event in node:
        if event["type"] == "INPUT":
            if event["id"] == "chassis_status":
                status = event["value"]
                if isinstance(status, bytes):
                    status = status.decode("utf-8")
                status = json.loads(status)
                print(f"收到底盘状态: {status}")
                if status.get("action") == "MOVE_COMPLETE":
                    node.send_output("next_action", json.dumps({"action": "MOVE_COMPLETE"}).encode())
            elif event["id"] == "arm_status":
                status = event["value"]
                if isinstance(status, bytes):
                    status = status.decode("utf-8")
                status = json.loads(status)
                print(f"收到机械臂状态: {status}")
                if status.get("action") == "GRAB_COMPLETE":
                    node.send_output("next_action", json.dumps({"action": "GRAB_COMPLETE"}).encode())
                elif status.get("action") == "RETURN_COMPLETE":
                    node.send_output("next_action", json.dumps({"action": "RETURN_COMPLETE"}).encode())

if __name__ == "__main__":
    main()