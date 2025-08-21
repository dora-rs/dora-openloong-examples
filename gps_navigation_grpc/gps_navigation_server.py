import grpc
from concurrent import futures
import time

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import proto.gps_navigation_pb2 as gps_navigation_pb2
import proto.gps_navigation_pb2_grpc as gps_navigation_pb2_grpc
from google.protobuf import empty_pb2

class NaviControllerServicer(gps_navigation_pb2_grpc.GPSNaviController):
    def setDestination(self, request, context):
        print("Received setDestination:", request)
        return gps_navigation_pb2.Response(succeeded=True, msg="Destination set")

    def startNavi(self, request, context):
        print("Received startNavi:", request)
        for i in range(3):
            yield gps_navigation_pb2.NaviResponse(
                succeeded=True,
                msg=f"Step {i}",
                arrived=(i == 2),
                state=gps_navigation_pb2.State(
                    position=gps_navigation_pb2.Descartes(x=i, y=i, z=0),
                    velocity=gps_navigation_pb2.Descartes(x=0, y=0, z=0),
                    attitude=gps_navigation_pb2.Euler(roll=0, pitch=0, yaw=0)
                )
            )
            time.sleep(1)

    def stopNavi(self, request, context):
        print("Received stopNavi")
        return gps_navigation_pb2.Response(succeeded=True, msg="Navigation stopped")

    def getState(self, request, context):
        print("Received getState")
        return gps_navigation_pb2.State(
            position=gps_navigation_pb2.Descartes(x=1, y=2, z=3),
            velocity=gps_navigation_pb2.Descartes(x=0, y=0, z=0),
            attitude=gps_navigation_pb2.Euler(roll=0, pitch=0, yaw=0)
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gps_navigation_pb2_grpc.add_GPSNaviControllerServicer_to_server(NaviControllerServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Server started at :50051")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()