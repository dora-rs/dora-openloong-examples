import os
import subprocess
import time
from dora import Node


def main():
    node = Node()
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "loong_sim_sdk_release", "tools")
    tools_dir = os.path.abspath(tools_dir)
    print(f"[sim_runner] tools_dir={tools_dir}")

    # Start sim
    proc = subprocess.Popen(["bash", "-lc", f"cd '{tools_dir}' && ./run_sim.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[sim_runner] started sim pid={proc.pid}")

    # Give it a moment to boot
    time.sleep(1.0)

    node.send_output("sim_ready", b"1")
    print("[sim_runner] sim_ready sent")

    # Keep node alive
    for _ in node:
        pass


if __name__ == "__main__":
    main()
