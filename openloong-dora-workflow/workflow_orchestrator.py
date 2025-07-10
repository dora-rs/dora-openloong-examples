from dora import Node

class WorkflowOrchestratorNode(Node):
    def on_event(self, event):
        pass

if __name__ == "__main__":
    WorkflowOrchestratorNode().run()