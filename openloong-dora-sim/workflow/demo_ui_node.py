import json
import time
from dora import Node


def main():
    node = Node()
    print("[demo_ui] started; will orchestrate mani demo sequence")

    phase = 0
    sent = False
    for event in node:
        # Wait for start trigger
        if event["type"] == "INPUT" and event["id"] == "trigger":
            print("[demo_ui] trigger received")
            sent = False
            phase = 0

        if phase == 0 and not sent:
            # Send GRAB command
            cmd = {"action": "GRAB"}
            node.send_output("mani_command", json.dumps(cmd).encode())
            print("[demo_ui] sent GRAB")
            sent = True
        elif event["type"] == "INPUT" and event["id"] == "mani_status":
            status = event["value"]
            if type(status).__name__ == "UInt8Array":
                status = status.to_numpy().tobytes().decode("utf-8")
            elif hasattr(status, "tobytes"):
                status = status.tobytes().decode("utf-8")
            elif isinstance(status, bytes):
                status = status.decode("utf-8")
            elif isinstance(status, str):
                pass
            else:
                continue
            status = json.loads(status)
            print(f"[demo_ui] mani_status: {status}")

            if phase == 0 and status.get("action") == "GRAB" and status.get("status") == "SUCCESS":
                # Send RETURN next
                time.sleep(0.5)
                cmd = {"action": "RETURN"}
                node.send_output("mani_command", json.dumps(cmd).encode())
                print("[demo_ui] sent RETURN")
                phase = 1
            elif phase == 1 and status.get("action") == "RETURN" and status.get("status") == "SUCCESS":
                print("[demo_ui] demo completed")
                # End or loop; here we stop sending more
                phase = 2


if __name__ == "__main__":
    main()
