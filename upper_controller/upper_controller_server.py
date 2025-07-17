import grpc
from concurrent import futures
import time

import upper_controller_pb2, upper_controller_pb2_grpc
from google.protobuf import empty_pb2

class UpperControllerServicer(upper_controller_pb2_grpc.UpperControllerServicer):
    def sendEndAction(self, request, context):
        print("sendEndAction:", request)
        return upper_controller_pb2.Response(succeeded=True, msg="End action received")

    def recvEndState(self, request, context):
        print("recvEndState")
        return upper_controller_pb2.EndPayload(
            end=upper_controller_pb2.EndPose(left=[1.0, 2.0], right=[3.0, 4.0]),
            effector=upper_controller_pb2.EffectorPosition(left=[0.1, 0.2], right=[0.3, 0.4])
        )

    def sendArmAction(self, request, context):
        print("sendArmAction:", request)
        return upper_controller_pb2.Response(succeeded=True, msg="Arm action received")

    def recvArmState(self, request, context):
        print("recvArmState")
        return upper_controller_pb2.ArmPayload(
            arm=upper_controller_pb2.ArmPosition(left=[5.0, 6.0], right=[7.0, 8.0]),
            effector=upper_controller_pb2.EffectorPosition(left=[0.5, 0.6], right=[0.7, 0.8])
        )

    def setConfig(self, request, context):
        print("setConfig:", request)
        return upper_controller_pb2.Response(succeeded=True, msg="Config set")

    def getConfig(self, request, context):
        print("getConfig")
        return upper_controller_pb2.Config(
            incharge=1, filter_level=2, arm_mode=3, digit_mode=4, neck_mode=5, waist_mode=6
        )

    def setNeckPose(self, request, context):
        print("setNeckPose:", request)
        return upper_controller_pb2.Response(succeeded=True, msg="Neck pose set")

    def getNeckPose(self, request, context):
        print("getNeckPose")
        return upper_controller_pb2.NeckPose(neck=[1.23])

    def setWaistPose(self, request, context):
        print("setWaistPose:", request)
        return upper_controller_pb2.Response(succeeded=True, msg="Waist pose set")

    def getWaistPose(self, request, context):
        print("getWaistPose")
        return upper_controller_pb2.WaistPose(waist=[4.56])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    upper_controller_pb2_grpc.add_UpperControllerServicer_to_server(UpperControllerServicer(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Server started at :50052")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()