#!/usr/bin/env python3
# coding=utf-8
'''=========== ***doc description @ yyp*** ===========
Copyright 2025 国地共建人形机器人创新中心/人形机器人（上海）有限公司, https://www.openloong.net/
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
Author: YYP

shm通信，仅可单机运行，亚毫秒级延时

======================================================'''
import ctypes
import os
import platform
from loong_jnt_sdk_datas import jntSdkSensDataClass, jntSdkCtrlDataClass

# ===========================
class jntSdkClass:
	def __init__(self, jntNum, fingerDofLeft, fingerDofRight):
		if(os.path.exists('../config/driver.ini')==0):
			print("共享内存版需匹配当前所在目录层级，保证可以按 ../config/driver.ini 路径访问")
			exit()
		path=os.path.dirname(os.path.abspath(__file__))
		if(platform.machine()=="x86_64" or platform.machine()=="amd64"):
			self.lib=ctypes.CDLL(path+'/lib/libloong_jnt_sdk_shm_x64.so')
		else:
			self.lib=ctypes.CDLL(path+'/lib/libloong_jnt_sdk_shm_a64.so')
		self.lib.initShmMode()
		self.libCtrlDataSize=self.lib.getCtrlDataSize()
		self.libSensDataSize=self.lib.getSensDataSize()

		self.sens=jntSdkSensDataClass(jntNum, fingerDofLeft, fingerDofRight)
		self.sensBuf=bytes(self.libSensDataSize)

	def send(self,ctrl:jntSdkCtrlDataClass):
		buf=ctrl.packData()
		if(len(buf) == self.libCtrlDataSize):
			self.lib.setCtrl(buf)
	def waitSens(self):
		pass
	def recv(self)->jntSdkSensDataClass:
		self.lib.getSens(self.sensBuf)
		self.sens.unpackData(self.sensBuf)
		return self.sens
	
	# def loopTimeAdapt(self,hz):
	# 	self.lib.loopTimeAdapt(ctypes.c_float(hz))
	

