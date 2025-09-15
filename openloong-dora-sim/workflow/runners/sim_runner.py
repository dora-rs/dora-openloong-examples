import os
import subprocess
import time
from dora import Node


def main():
    # print("=" * 60)
    # print("🚀 SIM_RUNNER 节点启动中...")
    # print("=" * 60)
    
    node = Node()
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "..", "loong_sim_sdk_release", "tools")
    tools_dir = os.path.abspath(tools_dir)
    # print(f"📁 [sim_runner] 工具目录: {tools_dir}")

    # Start sim
    # print("🔄 [sim_runner] 正在启动仿真器...")
    # 仿真器需要在bin目录下运行
    bin_dir = os.path.join(tools_dir, "..", "bin")
    arch = "x64" if os.uname().machine == "x86_64" else "a64"
    sim_bin = os.path.join(bin_dir, f"loong_share_sim_{arch}")
    # print(f"🚀 [sim_runner] 使用二进制文件: {sim_bin}")
    # print(f"📁 [sim_runner] 工作目录: {bin_dir}")
    
    # 在正确的目录下启动仿真器，设置DISPLAY环境变量
    env = os.environ.copy()
    env['DISPLAY'] = ':0'
    proc = subprocess.Popen([sim_bin], cwd=bin_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    print(f"✅ [sim_runner] 仿真器已启动，进程ID: {proc.pid}")

    # Give it a moment to boot
    # print("⏳ [sim_runner] 等待仿真器初始化...")
    time.sleep(1.0)

    node.send_output("sim_ready", b"1")
    # print("🎯 [sim_runner] 仿真器就绪信号已发送!")
    # print("=" * 60)
    # print("✅ SIM_RUNNER 节点运行中，等待其他节点...")
    # print("=" * 60)

    # Keep node alive
    # print("🔄 [sim_runner] 保持节点运行状态...")
    try:
        for event in node:
            # 处理任何输入事件（如果有的话）
            if event["type"] == "INPUT":
                print(f"📨 [sim_runner] 收到输入事件: {event['id']}")
            # 继续运行，不要退出
            pass
    except KeyboardInterrupt:
        print("🛑 [sim_runner] 收到中断信号，正在关闭...")
        if proc.poll() is None:
            print("🔄 [sim_runner] 正在终止仿真器进程...")
            proc.terminate()
            proc.wait()
    except Exception as e:
        print(f"❌ [sim_runner] 发生错误: {e}")
        if proc.poll() is None:
            print("🔄 [sim_runner] 正在终止仿真器进程...")
            proc.terminate()
            proc.wait()
    # finally:
        # print("🔚 [sim_runner] 节点正在退出...")
        # if proc.poll() is None:
        #     print("🔄 [sim_runner] 正在终止仿真器进程...")
            # proc.terminate()
            # proc.wait()


if __name__ == "__main__":
    main()
