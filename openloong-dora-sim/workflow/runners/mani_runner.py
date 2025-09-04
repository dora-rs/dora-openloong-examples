import os
import subprocess
import time
from dora import Node


def main():
    node = Node()
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "loong_sim_sdk_release", "tools")
    tools_dir = os.path.abspath(tools_dir)
    print(f"[mani_runner] tools_dir={tools_dir}")

    proc = subprocess.Popen(["bash", "-lc", f"cd '{tools_dir}' && ./run_manipulation.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[mani_runner] started manipulation pid={proc.pid}")

    time.sleep(1.0)
    node.send_output("mani_ready", b"1")
    print("[mani_runner] mani_ready sent")

    for _ in node:
        pass


if __name__ == "__main__":
    main()
