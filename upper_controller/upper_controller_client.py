import grpc
import upper_controller_pb2, upper_controller_pb2_grpc
from google.protobuf import empty_pb2

def run():
    channel = grpc.insecure_channel('localhost:50052')
    stub = upper_controller_pb2_grpc.UpperControllerStub(channel)

    # sendEndAction
    end_payload = upper_controller_pb2.EndPayload(
        end=upper_controller_pb2.EndPose(left=[1.0, 2.0], right=[3.0, 4.0]),
        effector=upper_controller_pb2.EffectorPosition(left=[0.1, 0.2], right=[0.3, 0.4])
    )
    resp = stub.sendEndAction(end_payload)
    print("sendEndAction:", resp)

    # recvEndState
    end_state = stub.recvEndState(empty_pb2.Empty())
    print("recvEndState:", end_state)

    # sendArmAction
    arm_payload = upper_controller_pb2.ArmPayload(
        arm=upper_controller_pb2.ArmPosition(left=[5.0, 6.0], right=[7.0, 8.0]),
        effector=upper_controller_pb2.EffectorPosition(left=[0.5, 0.6], right=[0.7, 0.8])
    )
    resp = stub.sendArmAction(arm_payload)
    print("sendArmAction:", resp)

    # recvArmState
    arm_state = stub.recvArmState(empty_pb2.Empty())
    print("recvArmState:", arm_state)

    # setConfig
    config = upper_controller_pb2.Config(
        incharge=1, filter_level=2, arm_mode=3, digit_mode=4, neck_mode=5, waist_mode=6
    )
    resp = stub.setConfig(config)
    print("setConfig:", resp)

    # getConfig
    config_resp = stub.getConfig(empty_pb2.Empty())
    print("getConfig:", config_resp)

    # setNeckPose
    neck_pose = upper_controller_pb2.NeckPose(neck=[1.23])
    resp = stub.setNeckPose(neck_pose)
    print("setNeckPose:", resp)

    # getNeckPose
    neck_pose_resp = stub.getNeckPose(empty_pb2.Empty())
    print("getNeckPose:", neck_pose_resp)

    # setWaistPose
    waist_pose = upper_controller_pb2.WaistPose(waist=[4.56])
    resp = stub.setWaistPose(waist_pose)
    print("setWaistPose:", resp)

    # getWaistPose
    waist_pose_resp = stub.getWaistPose(empty_pb2.Empty())
    print("getWaistPose:", waist_pose_resp)

if __name__ == '__main__':
    run()