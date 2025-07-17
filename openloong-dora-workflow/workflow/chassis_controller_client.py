import json
from dora import Node

def main():
    node = Node()
    print("底盘控制节点启动")
    for event in node:
        if event["type"] == "INPUT" and event["id"] == "chassis_command":
            print("收到底盘命令: ", event)
            cmd = event["value"]
            # 兼容 pyarrow.lib.UInt8Array、bytes、str
            if type(cmd).__name__ == "UInt8Array":
                # 用 to_numpy().tobytes() 转为 bytes
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
            print(f"收到底盘命令: {cmd}")
            # 这里应调用底盘server接口，模拟直接返回完成
            status = {"action": "MOVE_COMPLETE"}
            node.send_output("chassis_status", json.dumps(status).encode())

if __name__ == "__main__":
    main()