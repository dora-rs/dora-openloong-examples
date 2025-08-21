from dora import Node

def main():
    node = Node()
    print("机器人工作流触发节点启动")
    node.send_output("trigger", b"start")
    for _ in node:
        pass  # 保持节点运行

if __name__ == "__main__":
    main()