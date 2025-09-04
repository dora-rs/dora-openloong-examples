import os
import subprocess
import time
from dora import Node


def main():
    node = Node()
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "loong_sim_sdk_release", "tools")
    tools_dir = os.path.abspath(tools_dir)
    print(f"[interface_runner] tools_dir={tools_dir}")

    proc = subprocess.Popen(["bash", "-lc", f"cd '{tools_dir}' && ./run_interface.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[interface_runner] started interface pid={proc.pid}")

    time.sleep(1.0)
    node.send_output("interface_ready", b"1")
    print("[interface_runner] interface_ready sent")

    for _ in node:
        pass


if __name__ == "__main__":
    main()
