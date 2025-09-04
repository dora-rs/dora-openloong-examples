import os
import subprocess
import time
from dora import Node


def main():
    node = Node()
    tools_dir = os.path.join(os.path.dirname(__file__), "..", "loong_sim_sdk_release", "tools")
    tools_dir = os.path.abspath(tools_dir)
    print(f"[driver_runner] tools_dir={tools_dir}")

    proc = subprocess.Popen(["bash", "-lc", f"cd '{tools_dir}' && ./run_driver.sh"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[driver_runner] started driver pid={proc.pid}")

    time.sleep(1.0)
    node.send_output("driver_ready", b"1")
    print("[driver_runner] driver_ready sent")

    for _ in node:
        pass


if __name__ == "__main__":
    main()
