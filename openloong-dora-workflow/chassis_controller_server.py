import grpc
from concurrent import futures
import time

import proto.chassis_controller_pb2 as chassis_controller_pb2
import proto.chassis_controller_pb2_grpc as chassis_controller_pb2_grpc

class ChassisControlerServicer(chassis_controller_pb2_grpc.ChassisControlerServicer):
    def sendCommand(self, request, context):
        print("收到指令:")
        print(f"linear: x={request.linear.x}, y={request.linear.y}, z={request.linear.z}")
        print(f"angular: x={request.angular.x}, y={request.angular.y}, z={request.angular.z}")
        print(f"tap: {request.tap}, zOff: {request.zOff}")
        return chassis_controller_pb2.Response(succeeded=True, msg="Chassis action received")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chassis_controller_pb2_grpc.add_ChassisControlerServicer_to_server(ChassisControlerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("ChassisControler gRPC 服务器已启动，监听端口 50051")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()