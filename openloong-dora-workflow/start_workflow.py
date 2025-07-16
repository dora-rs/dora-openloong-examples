from dora import Node

def main():
    node = Node()
    print("🤖 机器人工作流触发节点启动")
    for event in node:
        node.send_output("trigger")
        break  # 只触发一次，触发后退出

if __name__ == "__main__":
    main()