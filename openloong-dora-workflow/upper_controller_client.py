import json
from dora import Node

def main():
    node = Node()
    print("🤖 上位机控制节点启动")
    for event in node:
        if event["type"] == "INPUT" and event["id"] == "arm_command":
            print("收到机械臂命令: ", event)
            cmd = event["value"]
            # 兼容 pyarrow.lib.UInt8Array、bytes、str
            if type(cmd).__name__ == "UInt8Array":
                cmd = cmd.to_numpy().tobytes().decode("utf-8")
            elif hasattr(cmd, "tobytes"):
                cmd = cmd.tobytes().decode("utf-8")
            elif isinstance(cmd, bytes):
                cmd = cmd.decode("utf-8")
            elif isinstance(cmd, str):
                pass
            else:
                raise TypeError(f"未知类型: {type(cmd)}")
            cmd = json.loads(cmd)
            print(f"收到机械臂命令: {cmd}")
            # 这里应调用机械臂server接口，模拟直接返回完成
            if cmd.get("action") == "GRAB":
                status = {"action": "GRAB_COMPLETE"}
            elif cmd.get("action") == "RETURN":
                status = {"action": "RETURN_COMPLETE"}
            else:
                status = {"action": "UNKNOWN"}
            node.send_output("arm_status", json.dumps(status).encode())

if __name__ == "__main__":
    main()