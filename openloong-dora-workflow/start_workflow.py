from dora import Node

class StartTriggerNode(Node):
    def __init__(self):
        super().__init__()
        self.triggered = False

    def on_event(self, event):
        if not self.triggered:
            self.send_output("start_trigger", b"start")
            self.triggered = True

if __name__ == "__main__":
    StartTriggerNode().run()