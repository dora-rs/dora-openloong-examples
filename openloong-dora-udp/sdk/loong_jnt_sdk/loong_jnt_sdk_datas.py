#!/usr/bin/env python3
# coding=utf-8
'''=========== ***doc description @ yyp*** ===========
Copyright 2025 国地共建人形机器人创新中心/人形机器人（上海）有限公司, https://www.openloong.net/
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
Author: YYP

青龙关节顺序：左臂7 右臂7 颈2 腰3 左腿6 右腿6
传感：
	int dataSize;			//数据帧c++散装内存大小
	double timestamp;		//epoch后秒数
	short key[2];			//遥控按键，当前所在plan之key
	char planName[16];		//当前所在plan之name
	short state[2];			//运行状态，任务状态
	float joy[4];			//遥控摇杆，可用于vx、vy、wz、zOff

	vec3f rpy,gyr,acc;		//imu
	vecXf actJ,actW,actT;	//实际关节角度、角速度、扭矩[左臂+右臂+颈+腰+左腿+右腿]
	vecXs drvTemp,drvState,drvErr;//驱动器温度、状态字、错误码[左臂+右臂+颈+腰+左腿+右腿]
	vecXf tgtJ,tgtW,tgtT;	//目标关节角度、角速度、扭矩[左臂+右臂+颈+腰+左腿+右腿]
	vecXf actFingerLeft, actFingerRight, tgtFingerLeft,  tgtFingerRight;//手指角度
命令：
	short checker;			//约定值（interface.ini内定义）
	short size;				//c++散装内存大小
	int state;				//0不执行，
	float torLimitRate=0.1;	//关节输出最大电流限制[0~1]
	float filtRate=0.05;	//滤波系数[0~1]，不是截止频率！输出=filtRate*输入 +(1-filtRate)*上一次输出
	vecXf j,w,t,kp,kd;
	vecXf fingerLeft, fingerRight;
======================================================'''
import struct
import numpy as np


class jntSdkSensDataClass:
	def __init__(self,jntNum, fingerDofLeft, fingerDofRight):
		# ！！！顺序不能乱！！！！
		self.size=np.zeros(1, np.int32)
		self.timestamp=np.zeros(1, np.float64)
		self.key=np.zeros(2, np.int16)
		self.planName:str="none"
		self.state=np.zeros(2, np.int16)
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

		self.__fmts=['i','d','2h','16s','2h','4f']
		self.__fmts.extend([f'3f']*3)
		self.__fmts.extend([f'{jntNum}f']*3)#j w t
		self.__fmts.extend([f'{jntNum}h']*3)#temp state err
		self.__fmts.extend([f'{jntNum}f']*3)#j w t
		self.__fmts.extend([f'{fingerDofLeft}f'])
		self.__fmts.extend([f'{fingerDofRight}f'])
		self.__fmts.extend([f'{fingerDofLeft}f'])
		self.__fmts.extend([f'{fingerDofRight}f'])

		self.__fmtSizes=[]
		for it in self.__fmts:
			self.__fmtSizes.append(struct.calcsize(it))

		np.set_printoptions(suppress=1, threshold=np.inf)
	def print(self):
		print("============")
		for it in self.__dict__:
			if it.startswith("_"):
				continue
			print(it,'=',self.__dict__[it])
	def unpackData(self,buf):
		# 务必注意c++的自动内存对齐，数据连续问题
		keys=list(self.__dict__.keys())
		idx=0
		for i in range(len(self.__fmts)):
			setattr(self, keys[i], np.array(struct.unpack(self.__fmts[i], buf[idx : idx+self.__fmtSizes[i]] )))
			idx+=self.__fmtSizes[i]
		self.planName =self.planName.tobytes().decode('utf-8')
		
# ====================================
class jntSdkCtrlDataClass:
	def __init__(self, jntNum, fingerDofLeft, fingerDofRight):
		self.checker	=3480	#short
		self.size		=16 +jntNum*4*5 +(fingerDofLeft+fingerDofRight)*4	#short
		self.state		=0
		self.torLimitRate=0.2
		self.filtRate	=0.05
		self.j=self.getStdJnt()
		self.w=np.zeros(jntNum, np.float32)
		self.t=np.zeros(jntNum, np.float32)
		self.kp=np.zeros(jntNum, np.float32)
		self.kd=np.zeros(jntNum, np.float32)
		self.fingerLeft=np.zeros(fingerDofLeft, np.float32)
		self.fingerRight=np.zeros(fingerDofRight, np.float32)
		self.reset()
	def reset(self):
		self.state		=0
		self.torLimitRate=0.2
		self.filtRate	=0.05
		self.j=self.getStdJnt()
		self.w.fill(0)
		self.t.fill(0)
		self.kp.fill(0)
		self.kd.fill(0)
		self.fingerLeft.fill(0)
		self.fingerRight.fill(0)
	def getStdJnt(self):
		return np.array([
			0.3,-1.3, 1.8, 0.5, 0,0,0,
			-0.3,-1.3,-1.8, 0.5, 0,0,0,
			0,0,0,0,0,
			0.0533331, 0, 0.325429, -0.712646, 0.387217,-0.0533331, 
			-0.0533331, 0, 0.325429, -0.712646, 0.387217, 0.0533331], np.float32)
	def packData(self):
		buf=struct.pack('2hi', self.checker, self.size, self.state)
		buf+=struct.pack('ff', self.torLimitRate, self.filtRate)
		buf+=self.j.astype(dtype=np.float32).tobytes()
		buf+=self.w.astype(dtype=np.float32).tobytes()
		buf+=self.t.astype(dtype=np.float32).tobytes()
		buf+=self.kp.astype(dtype=np.float32).tobytes()
		buf+=self.kd.astype(dtype=np.float32).tobytes()
		buf+=self.fingerLeft.astype(dtype=np.float32).tobytes()
		buf+=self.fingerRight.astype(dtype=np.float32).tobytes()
		if(len(buf)!=self.size):
			print("jntSdk ctrl数据打包大小不匹配！",len(buf),self.size)
			exit()
		return buf
