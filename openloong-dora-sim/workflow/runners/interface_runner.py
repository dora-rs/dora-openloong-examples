import os
import subprocess
import time
from dora import Node


def main():
    print("=" * 60)
    print("🔌 INTERFACE_RUNNER 节点启动中...")
    print("=" * 60)
    
    node = Node()
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "..", "loong_sim_sdk_release", "tools")
    tools_dir = os.path.abspath(tools_dir)
    print(f"📁 [interface_runner] 工具目录: {tools_dir}")

    print("🔄 [interface_runner] 正在启动接口程序...")
    # 接口程序需要在bin目录下运行
    bin_dir = os.path.join(tools_dir, "..", "bin")
    arch = "x64" if os.uname().machine == "x86_64" else "a64"
    interface_bin = os.path.join(bin_dir, f"loong_interface_{arch}")
    print(f"🔌 [interface_runner] 使用二进制文件: {interface_bin}")
    print(f"📁 [interface_runner] 工作目录: {bin_dir}")
    
    # 在正确的目录下启动接口程序
    proc = subprocess.Popen([interface_bin], cwd=bin_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"✅ [interface_runner] 接口程序已启动，进程ID: {proc.pid}")

    print("⏳ [interface_runner] 等待接口程序初始化...")
    time.sleep(1.0)
    
    node.send_output("interface_ready", b"1")
    print("🎯 [interface_runner] 接口就绪信号已发送!")
    print("=" * 60)
    print("✅ INTERFACE_RUNNER 节点运行中，等待其他节点...")
    print("=" * 60)

    # Keep node alive
    try:
        print("🔄 [interface_runner] 保持节点运行状态...")
        while True:
            try:
                event = next(node)
                if event["type"] == "INPUT":
                    print(f"📨 [interface_runner] 收到输入事件: {event['id']}")
                    if event["id"] == "driver_ready":
                        node.send_output("interface_ready", b"1")
                        print("🔁 [interface_runner] 已响应 driver_ready")
            except StopIteration:
                # print("🔁 [interface_runner] 节点暂时无事件，继续等待...")
                time.sleep(0.1)  # 避免 CPU 占用过高
    except KeyboardInterrupt:
        print("🛑 [interface_runner] 收到中断信号，正在关闭...")
        if proc.poll() is None:
            print("🔄 [interface_runner] 正在终止接口程序进程...")
            proc.terminate()
            proc.wait()
    except Exception as e:
        print(f"❌ [interface_runner] 发生错误: {e}")
        if proc.poll() is None:
            print("🔄 [interface_runner] 正在终止接口程序进程...")
            proc.terminate()
            proc.wait()
    # finally:
    #     print("🔚 [interface_runner] 节点正在退出...")
    #     if proc.poll() is None:
    #         print("🔄 [interface_runner] 正在终止接口程序进程...")
    #         proc.terminate()
    #         proc.wait()


if __name__ == "__main__":
    main()
