from google.protobuf import empty_pb2 as _empty_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Descartes(_message.Message):
    __slots__ = ("x", "y", "z")
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class Euler(_message.Message):
    __slots__ = ("roll", "pitch", "yaw")
    ROLL_FIELD_NUMBER: _ClassVar[int]
    PITCH_FIELD_NUMBER: _ClassVar[int]
    YAW_FIELD_NUMBER: _ClassVar[int]
    roll: float
    pitch: float
    yaw: float
    def __init__(self, roll: _Optional[float] = ..., pitch: _Optional[float] = ..., yaw: _Optional[float] = ...) -> None: ...

class Pose(_message.Message):
    __slots__ = ("position", "attitude")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    ATTITUDE_FIELD_NUMBER: _ClassVar[int]
    position: Descartes
    attitude: Euler
    def __init__(self, position: _Optional[_Union[Descartes, _Mapping]] = ..., attitude: _Optional[_Union[Euler, _Mapping]] = ...) -> None: ...

class State(_message.Message):
    __slots__ = ("position", "velocity", "attitude")
    POSITION_FIELD_NUMBER: _ClassVar[int]
    VELOCITY_FIELD_NUMBER: _ClassVar[int]
    ATTITUDE_FIELD_NUMBER: _ClassVar[int]
    position: Descartes
    velocity: Descartes
    attitude: Euler
    def __init__(self, position: _Optional[_Union[Descartes, _Mapping]] = ..., velocity: _Optional[_Union[Descartes, _Mapping]] = ..., attitude: _Optional[_Union[Euler, _Mapping]] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("succeeded", "msg")
    SUCCEEDED_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    succeeded: bool
    msg: str
    def __init__(self, succeeded: bool = ..., msg: _Optional[str] = ...) -> None: ...

class NaviResponse(_message.Message):
    __slots__ = ("succeeded", "msg", "arrived", "state")
    SUCCEEDED_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    ARRIVED_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    succeeded: bool
    msg: str
    arrived: bool
    state: State
    def __init__(self, succeeded: bool = ..., msg: _Optional[str] = ..., arrived: bool = ..., state: _Optional[_Union[State, _Mapping]] = ...) -> None: ...
