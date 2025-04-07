# -*- coding: utf-8 -*-
"""
Data acquisition and assembly demo in SCADA
"""

import urllib2
import json
import time
import traceback as tb

class Client():
    def __init__(self):
        self.BUFFER = {}
    
    def process_data(self, machineNo, BUFFER_SIZE):
    	
        # 读取当前数据
        current_data = {
        	"machineNo": machineNo,
            "error_Op": system.tag.read(u"[default]" + machineNo + "/LLM_Test/error_Op").value,
            "Gap_Op": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Gap_Op").value,
            "Kp_Op": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Kp_Op").value,
            "Ki_Op": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Ki_Op").value,
            "Kd_Op": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Kd_Op").value,
            "out_Op": system.tag.read(u"[default]" + machineNo + "/LLM_Test/out_Op").value,
            
            "error_Dri": system.tag.read(u"[default]" + machineNo + "/LLM_Test/error_Dri").value,
            "Gap_Dri": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Gap_Dri").value,
            "Kp_Dri": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Kp_Dri").value,
            "Ki_Dri": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Ki_Dri").value,
            "Kd_Dri": system.tag.read(u"[default]" + machineNo + "/LLM_Test/Kd_Dri").value,
            "out_Dri": system.tag.read(u"[default]" + machineNo + "/LLM_Test/out_Dri").value,
            
            "speed": system.tag.read(u"[default]" + machineNo + "/LLM_Test/speed").value
        }
        
        # 初始化
        if len(self.BUFFER.keys()) == 0:
        	for key in list(current_data.keys()):
        		self.BUFFER[key] = []
        		self.BUFFER[key].append(current_data[key])
        	return 0
        		
        # 初始化完成
        else:
            keys = list(self.BUFFER.keys())
            key = keys[0]
            
            # 收集数组
            if len(self.BUFFER[key]) < BUFFER_SIZE:
                for key in keys:
                    self.BUFFER[key].append(current_data[key])
                    
                # print(self.BUFFER)
            	return 0
            
            
            # 数组已满，可发送
            try:
            	SendData = self.BUFFER.copy()
                # 清空数组
                keys = list(self.BUFFER.keys())
                for key in keys:
                    self.BUFFER[key] = []
                return SendData

            except Exception as e:
                print("通信异常:", str(e))
                print(str(tb.format_exc()))

    
    
    
