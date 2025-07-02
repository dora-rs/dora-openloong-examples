import grpc
import gps_navigation_pb2
import gps_navigation_pb2_grpc
from google.protobuf import empty_pb2

def run():
    print("waiting for server...")
    channel = grpc.insecure_channel('localhost:50051')
    navi_stub = gps_navigation_pb2_grpc.GPSNaviControllerStub(channel)
    print("connected to server")
    print("current state:", navi_stub.getState(empty_pb2.Empty()))
    
    # setDestination
    pose = gps_navigation_pb2.Pose(
        position=gps_navigation_pb2.Descartes(x=1, y=2, z=0),
        attitude=gps_navigation_pb2.Euler(roll=0, pitch=0, yaw=1.57)
    )
    resp = navi_stub.setDestination(pose)
    print("setDestination:", resp)

    # startNavi
    for navi_resp in navi_stub.startNavi(empty_pb2.Empty()):
        print("startNavi:", navi_resp)
        if navi_resp.arrived:
            break

    # stopNavi
    resp = navi_stub.stopNavi(empty_pb2.Empty())
    print("stopNavi:", resp)

    # getState
    state = navi_stub.getState(empty_pb2.Empty())
    print("getState:", state)


if __name__ == '__main__':
    run()
