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

def send_joint_command(node):
    command = {
        "action": "JOINT_CONTROL",
        "state": 1,
        "tor_limit_rate": 0.2,
        "filt_rate": 0.05,
        "joint_angles": [0.3, -1.3, 1.8, 0.5, 0, 0, 0,  # 左臂
                        -0.3, -1.3, -1.8, 0.5, 0, 0, 0,  # 右臂
                        0, 0, 0, 0, 0,  # 颈
                        0.0533331, 0, 0.325429, -0.712646, 0.387217, -0.0533331,  # 左腿
                        -0.0533331, 0, 0.325429, -0.712646, 0.387217, 0.0533331],  # 右腿
        "finger_left": [0.0, 0.0, 0.0],
        "finger_right": [0.0, 0.0, 0.0]
    }
    node.send_output("joint_command", json.dumps(command).encode())
    print("发送关节控制命令")

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
    # 将抓取命令转换为 loong_mani_client 可识别的字段
    command = {
        "action": "GRAB",
        "mode": "joint_control",           # 关节轴控
        # 可选：臂角度命令（保留默认即可）
        # "arm_cmd": [[...7 floats...], [...7 floats...]],
        "finger_left": [0.8, 0.8, 0.8],     # 抓取闭合
        "finger_right": [0.8, 0.8, 0.8],
        "neck_cmd": [0.0, 0.0],
        "lumbar_cmd": [0.0]
    }
    node.send_output("mani_command", json.dumps(command).encode())
    print("发送机械臂抓取命令")

def send_return_command(node):
    command = {
        "action": "RETURN",
        "mode": "return_home",             # 回正模式
        # 可选：显式回正角度
        # "arm_cmd": [[0,0,0,0,0,0,0], [0,0,0,0,0,0,0]],
        "finger_left": [0.0, 0.0, 0.0],
        "finger_right": [0.0, 0.0, 0.0],
        "neck_cmd": [0.0, 0.0],
        "lumbar_cmd": [0.0]
    }
    node.send_output("mani_command", json.dumps(command).encode())
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
                send_joint_command(node)  # 同时发送关节控制命令
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