import os
import subprocess
import time
import select
from dora import Node


def main():
    # print("=" * 60)
    # print("🤖 MANI_RUNNER 节点启动中...")
    # print("=" * 60)
    
    node = Node()
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "..", "loong_sim_sdk_release", "tools")
    tools_dir = os.path.abspath(tools_dir)
    # print(f"📁 [mani_runner] 工具目录: {tools_dir}")

    # print("🔄 [mani_runner] 正在启动机械臂控制程序...")
    # 机械臂控制程序需要在bin目录下运行
    bin_dir = os.path.join(tools_dir, "..", "bin")
    arch = "x64" if os.uname().machine == "x86_64" else "a64"
    mani_bin = os.path.join(bin_dir, f"loong_manipulation_{arch}")
    # print(f"🤖 [mani_runner] 使用二进制文件: {mani_bin}")
    # print(f"📁 [mani_runner] 工作目录: {bin_dir}")
    
    # 在正确的目录下启动机械臂控制程序
    proc = subprocess.Popen(['sudo',mani_bin], cwd=bin_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print(f"✅ [mani_runner] 机械臂控制程序已启动，进程ID: {proc.pid}")

    print("⏳ [mani_runner] 等待机械臂控制程序初始化...")
    time.sleep(1.0)
    
    node.send_output("mani_ready", b"1")
    print("🎯 [mani_runner] 机械臂就绪信号已发送!")
    print("=" * 60)
    print("✅ MANI_RUNNER 节点运行中，等待其他节点...")
    print("=" * 60)
    try:
        print("🔄 [interface_runner] 保持节点运行状态...")
        while True:
            for pipe, name in [(proc.stdout, "stdout"), (proc.stderr, "stderr")]:
                rlist, _, _ = select.select([pipe], [], [], 0)
                if rlist:
                    line = pipe.readline()
                    if line:
                        print(f"[mani_bin {name}] {line.decode(errors='ignore').rstrip()}")
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
        print("🛑 [mani_runner] 收到中断信号，正在关闭...")
        if proc.poll() is None:
            print("🔄 [mani_runner] 正在终止机械臂控制程序进程...")
            proc.terminate()
            proc.wait()
    except Exception as e:
        print(f"❌ [mani_runner] 发生错误: {e}")
        if proc.poll() is None:
            print("🔄 [mani_runner] 正在终止机械臂控制程序进程...")
            proc.terminate()
            proc.wait()
    # finally:
    #     print("🔚 [mani_runner] 节点正在退出...")
    #     if proc.poll() is None:
    #         print("🔄 [mani_runner] 正在终止机械臂控制程序进程...")
    #         proc.terminate()
    #         proc.wait()


if __name__ == "__main__":
    main()
