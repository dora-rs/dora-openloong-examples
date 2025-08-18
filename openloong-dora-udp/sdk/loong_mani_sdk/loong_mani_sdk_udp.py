#!/usr/bin/env python3
# coding=utf-8
'''=========== ***doc description @ yyp*** ===========
Copyright 2025 国地共建人形机器人创新中心/人形机器人（上海）有限公司, https://www.openloong.net/
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
Author: YYP

传感：
	int dataSize;		//数据帧大小
	double timestamp	//epoch后秒数
	short key[2];		//遥控按键，当前所在plan之key
	char planName[16];	//当前所在plan之name
	short state[2];		//运行状态，任务状态
	float joy[4];		//遥控摇杆，可用于vx、vy、wz、zOff
	vec3f rpy,gyr,acc;	//imu
	vecXf actJ,actW,actT;			//实际关节角度、角速度、扭矩[左臂+右臂+颈+腰]
	vecXs drvTemp,drvState,drvErr;	//驱动器温度、状态字、错误码[左臂+右臂+颈+腰]
	vecXf tgtJ,tgtW,tgtT;			//目标关节角度、角速度、扭矩[左臂+右臂+颈+腰]
	vecXf actFingerLeft, actFingerRight, tgtFingerLeft,  tgtFingerRight;//手指角度
	vec6f actTipPRpy2B[2],actTipVW2B[2],actTipFM2B[2];	//实际末端(tip)的pos、rpy to B系(body)； vel、omega； force、moment
	vec6f tgtTipPRpy2B[2],tgtTipVW2B[2],tgtTipFM2B[2];	//目标末端(tip)的pos、rpy to B系(body)； vel、omega； force、moment
命令：
	short inCharge=1;	//当loco、mani同时运行，mani是否介入控制
	short filtLevel;	//滤波等级0~5，0最大滤波，>=5不滤波
	
	short armMode;		//0无，1回正，2下肢命令透传，3关节轴控，4笛卡尔身体系
	short fingerMode;	//0无，1回正，2下肢命令透传，3关节轴控，4伸直
	short neckMode;		//0无，1回正，2下肢命令透传，3关节轴控，4导航随动，5看左手，6看右手，7看双手中间
	short lumbarMode;	//0无，1回正，2下肢命令透传，3关节轴控，4姿态控制

	vecXf armCmd[2];	//armMode=2: xyz+rpy+臂型角。armMode=3: 轴控。至少6维，至多armDof
	vec6f armFM[2];		//前馈，3力+3扭，armMode=2、3时生效
	vecXf fingerCmd[2]; //fingerDof
	vecXf neckCmd;		//neckDof
	vecXf lumbarCmd;	//lumbarDof
======================================================'''
import socket
import struct
import numpy as np


class maniSdkSensDataClass:
	def __init__(self,jntNum,fingerDofLeft, fingerDofRight):
		self.dataSize=np.zeros(1, np.int32)
		self.timestamp=np.zeros(1, np.float64)
		self.key=np.zeros(2, np.int16) #short
		self.planName:str="none"
		self.state=np.zeros(2, np.int16) #short
		self.joy=np.zeros(4, np.float32)

		self.rpy=np.zeros(3, np.float32)
		self.gyr=np.zeros(3, np.float32)
		self.acc=np.zeros(3, np.float32)
		self.actJ=np.zeros(jntNum, np.float32)
		self.actW=np.zeros(jntNum, np.float32)
		self.actT=np.zeros(jntNum, np.float32)
		self.drvTemp=np.zeros(jntNum, np.int16)
		self.drvState=np.zeros(jntNum, np.int16)
		self.drvErr=np.zeros(jntNum, np.int16)
		self.tgtJ=np.zeros(jntNum, np.float32)
		self.tgtW=np.zeros(jntNum, np.float32)
		self.tgtT=np.zeros(jntNum, np.float32)

		self.actFingerLeft=np.zeros(fingerDofLeft, np.float32)
		self.actFingerRight=np.zeros(fingerDofRight, np.float32)
		self.tgtFingerLeft=np.zeros(fingerDofLeft, np.float32)
		self.tgtFingerRight=np.zeros(fingerDofRight, np.float32)

		self.actTipPRpy2B=np.zeros((2,6), np.float32)
		self.actTipVW2B  =np.zeros((2,6), np.float32)
		self.actTipFM2B  =np.zeros((2,6), np.float32)
		self.tgtTipPRpy2B=np.zeros((2,6), np.float32)
		self.tgtTipVW2B  =np.zeros((2,6), np.float32)
		self.tgtTipFM2B  =np.zeros((2,6), np.float32)

		self.__fmts=['i','d','2h','16s','2h','4f']
		self.__fmts.extend([f'3f']*3)
		self.__fmts.extend([f'{jntNum}f']*3)
		self.__fmts.extend([f'{jntNum}h']*3)
		self.__fmts.extend([f'{jntNum}f']*3)
		self.__fmts.extend([f'{fingerDofLeft}f'])
		self.__fmts.extend([f'{fingerDofRight}f'])
		self.__fmts.extend([f'{fingerDofLeft}f'])
		self.__fmts.extend([f'{fingerDofRight}f'])
		self.__fmts.extend(['12f']*6)

		self.__fmtSizes=[]
		for it in self.__fmts:
			self.__fmtSizes.append(struct.calcsize(it))
	def getFmts(self):
		return self.__fmts
	def getFmtSizes(self):
		return self.__fmtSizes
	def print(self):
		np.set_printoptions(suppress=True)
		print("============")
		for it in self.__dict__:
			if it.startswith("_"):
				continue
			print(it,'=',self.__dict__[it])

class maniSdkCtrlDataClass:
	def __init__(self, armDof, fingerDofLeft, fingerDofRight, neckDof, lumbarDof):
		self.inCharge=  1	#short
		self.filtLevel= 2	#short
		self.armMode=   0	#short
		self.fingerMode=0	#short
		self.neckMode=  5	#short
		self.lumbarMode=0	#short

		self.armCmd=   np.array([[0.4, 0.3, 0.1,   0,0,0,   0.5],
								[0.2,-0.3, 0.1,   0,0,0,   0.5]],np.float32)
		if(self.armCmd.shape[1]!=armDof):
			print('臂自由度不匹配！')
			exit()
		self.armFM=      np.zeros((2,6),np.float32)
		self.fingerLeft= np.zeros(fingerDofLeft, np.float32)
		self.fingerRight=np.zeros(fingerDofRight, np.float32)
		self.neckCmd=    np.zeros(neckDof,np.float32)
		self.lumbarCmd=  np.zeros(lumbarDof,np.float32)

		self.armDof=armDof
		self.fingerDofLeft=fingerDofLeft
		self.fingerDofRight=fingerDofRight
		self.neckDof=neckDof
		self.lumbarDof=lumbarDof


class maniSdkClass:
	def __init__(self, ip:str, port:int, jntNum, fingerDofLeft, fingerDofRight):
		self.rbtIpPort=(ip,port)
		self.sk=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sk.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1)
		self.sk.setblocking(0)
		self.sens=maniSdkSensDataClass(jntNum, fingerDofLeft, fingerDofRight)

	def send(self,ctrl:maniSdkCtrlDataClass):
		self.sk.sendto(self.packData(ctrl), self.rbtIpPort)
	def recv(self)->maniSdkSensDataClass:
		try:
			buf,_=self.sk.recvfrom(2048)
			self.unpackData(buf)
		except:
			pass
		return self.sens

	def unpackData(self,buf):
		# 务必注意c++的自动内存对齐，数据连续问题
		fmts=self.sens.getFmts()
		sizes=self.sens.getFmtSizes()
		keys=list(self.sens.__dict__.keys())
		idx=0
		for i in range(len(fmts)):
			setattr(self.sens, keys[i], np.array(struct.unpack(fmts[i],buf[idx:idx+sizes[i]])))
			idx+=sizes[i]
		self.sens.planName =self.sens.planName.tobytes().decode('utf-8')
		self.sens.actTipPRpy2B =self.sens.actTipPRpy2B.reshape((2,-1))
		self.sens.actTipVW2B =self.sens.actTipVW2B.reshape((2,-1))
		self.sens.actTipFM2B =self.sens.actTipFM2B.reshape((2,-1))
		self.sens.tgtTipPRpy2B =self.sens.tgtTipPRpy2B.reshape((2,-1))
		self.sens.tgtTipVW2B =self.sens.tgtTipVW2B.reshape((2,-1))
		self.sens.tgtTipFM2B =self.sens.tgtTipFM2B.reshape((2,-1))

	def packData(self, ctrl:maniSdkCtrlDataClass):
		buf=struct.pack('6h', ctrl.inCharge, ctrl.filtLevel, ctrl.armMode,
								ctrl.fingerMode, ctrl.neckMode, ctrl.lumbarMode)
		buf+=ctrl.armCmd.astype(dtype=np.float32).tobytes()
		buf+=ctrl.armFM.astype(dtype=np.float32).tobytes()
		buf+=ctrl.fingerLeft.astype(dtype=np.float32).tobytes()
		buf+=ctrl.fingerRight.astype(dtype=np.float32).tobytes()
		buf+=ctrl.neckCmd.astype(dtype=np.float32).tobytes()
		buf+=ctrl.lumbarCmd.astype(dtype=np.float32).tobytes()
		# if(len(buf)!=184):
		# 	print("maniSdk cmd数据udp打包大小不匹配！",len(buf))
		# 	exit()
		return buf

