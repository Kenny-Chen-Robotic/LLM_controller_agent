import subprocess
import json
import time
import traceback
import ast
import re

# 定义本地脚本路径和参数
script_path = r"C:\Users\52351\Desktop\LLM_control_ignition_PIDtuner.py"  # 使用原始字符串

machineNo = 'CalenderAnode11'
BUFFER_SIZE = 10
client = LLM_Data_Client.Client()

while 1:
	
	current_data = client.process_data(machineNo, BUFFER_SIZE)
	
	if current_data != 0:
		json_data = json.dumps(current_data)
		
		# 调用本地脚本
		try:
		    # 使用 subprocess.Popen 调用脚本
		    process = subprocess.Popen(
		    ["python", script_path], 
		    stdin=subprocess.PIPE,
		    stdout=subprocess.PIPE,  # 捕获标准输出
		    stderr=subprocess.PIPE   # 捕获标准错误)
		    )
		    
		    # 需要编码为bytes类型
		    stdout, stderr = process.communicate(input=json_data.encode())
		    print("Script output0: {0}, type: {1}".format(stdout, type(stdout)))
		        
		    # 有效数据的字符串还原成字典，也不是每步都会有输出
		    stdout = ast.literal_eval()(stdout)
		    
		    # 检查脚本是否成功执行
		    if process.returncode == 0:
		        print("Script output2: {0}, type: {1}".format(stdout, type(stdout)))
		    else:
		        print("Script failed with error:", stderr)
		    
		except Exception as e:
		    print("An error occurred:", str(e))
		    
	time.sleep(5)
    
    
    
    
    
    
    