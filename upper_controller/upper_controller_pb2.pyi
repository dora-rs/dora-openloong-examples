from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class EffectorPosition(_message.Message):
    __slots__ = ("left", "right")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    left: _containers.RepeatedScalarFieldContainer[float]
    right: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, left: _Optional[_Iterable[float]] = ..., right: _Optional[_Iterable[float]] = ...) -> None: ...

class EndPose(_message.Message):
    __slots__ = ("left", "right")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    left: _containers.RepeatedScalarFieldContainer[float]
    right: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, left: _Optional[_Iterable[float]] = ..., right: _Optional[_Iterable[float]] = ...) -> None: ...

class ArmPosition(_message.Message):
    __slots__ = ("left", "right")
    LEFT_FIELD_NUMBER: _ClassVar[int]
    RIGHT_FIELD_NUMBER: _ClassVar[int]
    left: _containers.RepeatedScalarFieldContainer[float]
    right: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, left: _Optional[_Iterable[float]] = ..., right: _Optional[_Iterable[float]] = ...) -> None: ...

class NeckPose(_message.Message):
    __slots__ = ("neck",)
    NECK_FIELD_NUMBER: _ClassVar[int]
    neck: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, neck: _Optional[_Iterable[float]] = ...) -> None: ...

class WaistPose(_message.Message):
    __slots__ = ("waist",)
    WAIST_FIELD_NUMBER: _ClassVar[int]
    waist: _containers.RepeatedScalarFieldContainer[float]
    def __init__(self, waist: _Optional[_Iterable[float]] = ...) -> None: ...

class EndPayload(_message.Message):
    __slots__ = ("end", "effector")
    END_FIELD_NUMBER: _ClassVar[int]
    EFFECTOR_FIELD_NUMBER: _ClassVar[int]
    end: EndPose
    effector: EffectorPosition
    def __init__(self, end: _Optional[_Union[EndPose, _Mapping]] = ..., effector: _Optional[_Union[EffectorPosition, _Mapping]] = ...) -> None: ...

class ArmPayload(_message.Message):
    __slots__ = ("arm", "effector")
    ARM_FIELD_NUMBER: _ClassVar[int]
    EFFECTOR_FIELD_NUMBER: _ClassVar[int]
    arm: ArmPosition
    effector: EffectorPosition
    def __init__(self, arm: _Optional[_Union[ArmPosition, _Mapping]] = ..., effector: _Optional[_Union[EffectorPosition, _Mapping]] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("succeeded", "msg")
    SUCCEEDED_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    succeeded: bool
    msg: str
    def __init__(self, succeeded: bool = ..., msg: _Optional[str] = ...) -> None: ...

class Config(_message.Message):
    __slots__ = ("incharge", "filter_level", "arm_mode", "digit_mode", "neck_mode", "waist_mode")
    INCHARGE_FIELD_NUMBER: _ClassVar[int]
    FILTER_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ARM_MODE_FIELD_NUMBER: _ClassVar[int]
    DIGIT_MODE_FIELD_NUMBER: _ClassVar[int]
    NECK_MODE_FIELD_NUMBER: _ClassVar[int]
    WAIST_MODE_FIELD_NUMBER: _ClassVar[int]
    incharge: int
    filter_level: int
    arm_mode: int
    digit_mode: int
    neck_mode: int
    waist_mode: int
    def __init__(self, incharge: _Optional[int] = ..., filter_level: _Optional[int] = ..., arm_mode: _Optional[int] = ..., digit_mode: _Optional[int] = ..., neck_mode: _Optional[int] = ..., waist_mode: _Optional[int] = ...) -> None: ...
