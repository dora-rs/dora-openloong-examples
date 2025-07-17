import json
from dora import Node

def send_chassis_command(node):
    command = {
        "action": "MOVE",
        "target": {"x": 1.0, "y": 0.0, "z": 0.0, "wz": 0.0},
        "tap": 0,
        "zOff": 0.0
    }
    node.send_output("chassis_command", json.dumps(command).encode())
    print("发送底盘移动命令")

def check_condition(node):
    condition_met = True
    if condition_met:
        print("条件满足，准备抓取")
        node.send_output("workflow_status", json.dumps({"status": "CONDITION_MET"}).encode())
        send_grab_command(node)  # 直接进入抓取流程
    else:
        print("条件不满足")
        node.send_output("workflow_status", json.dumps({"status": "CONDITION_NOT_MET"}).encode())

def send_grab_command(node):
    command = {
        "action": "GRAB",
        "target": {"left": [1.0, 2.0, 3.0], "right": [4.0, 5.0, 6.0]},
        "effector": {"left": [0.1, 0.2], "right": [0.3, 0.4]}
    }
    node.send_output("arm_command", json.dumps(command).encode())
    print("发送机械臂抓取命令")

def send_return_command(node):
    command = {
        "action": "RETURN",
        "target": {"left": [0.0, 0.0, 0.0], "right": [0.0, 0.0, 0.0]},
        "effector": {"left": [0.0, 0.0], "right": [0.0, 0.0]}
    }
    node.send_output("arm_command", json.dumps(command).encode())
    print("发送机械臂返回命令")

def send_completion_status(node):
    status = {
        "status": "COMPLETE",
        "message": "机器人工作流执行完成"
    }
    node.send_output("workflow_status", json.dumps(status).encode())
    print("机器人工作流执行完成")

def main():
    node = Node()
    print("机器人工作流run节点启动")
    workflow_state = "INIT"
    for event in node:
        print("事件触发:", event)
        if event["type"] == "INPUT":
            if event["id"] == "trigger":
                print("机器人工作流启动")
                workflow_state = "MOVE_TO_TARGET"
                send_chassis_command(node)
            elif event["id"] == "next_action":
                action_data = event["value"]
                # 兼容 pyarrow.lib.UInt8Array、bytes、str
                if type(action_data).__name__ == "UInt8Array":
                    action_data = action_data.to_numpy().tobytes().decode("utf-8")
                elif hasattr(action_data, "tobytes"):
                    action_data = action_data.tobytes().decode("utf-8")
                elif isinstance(action_data, bytes):
                    action_data = action_data.decode("utf-8")
                elif isinstance(action_data, str):
                    pass
                else:
                    raise TypeError(f"未知类型: {type(action_data)}")
                action = json.loads(action_data)
                print(f"收到下一步动作: {action}")
                if action.get("action") == "MOVE_COMPLETE":
                    workflow_state = "CHECK_CONDITION"
                    check_condition(node)
                elif action.get("action") == "CONDITION_MET":
                    workflow_state = "GRAB_OBJECT"
                    send_grab_command(node)
                elif action.get("action") == "GRAB_COMPLETE":
                    workflow_state = "RETURN_HOME"
                    send_return_command(node)
                elif action.get("action") == "RETURN_COMPLETE":
                    workflow_state = "COMPLETE"
                    send_completion_status(node)
                elif action.get("action") == "CONDITION_NOT_MET":
                    workflow_state = "COMPLETE"
                    print("条件不满足，工作流终止")
                    send_completion_status(node)

if __name__ == "__main__":
    main()