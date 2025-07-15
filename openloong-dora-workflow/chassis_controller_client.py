import json
from dora import Node

def main():
    node = Node()
    print("🚗 底盘控制节点启动")
    for event in node:
        if event["type"] == "INPUT" and event["id"] == "chassis_command":
            cmd = event["value"]
            if isinstance(cmd, bytes):
                cmd = cmd.decode("utf-8")
            cmd = json.loads(cmd)
            print(f"收到底盘命令: {cmd}")
            # 这里应调用底盘server接口，模拟直接返回完成
            status = {"action": "MOVE_COMPLETE"}
            node.send_output("chassis_status", json.dumps(status).encode())

if __name__ == "__main__":
    main()