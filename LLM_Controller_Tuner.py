# llm_service.py
'''
Demo of parameter tuner of calender closed-loop PID controller via LLM API
'''

import requests
import time
import sys
import json
import csv
import os
import ast
from datetime import datetime
import re

DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
API_KEY = YOUR-KEY

def process_with_llm(data):

    prompt = f"""锂电池辊缝模式辊压机工业控制优化建议生成：
当前设备的PID脚本为分误差阶梯设置的PID参数，PID为增量式PID，运行状态：
- 机台编号: {data['machineNo']}

- 辊压机的运行速度历史：{data['speed']}m/min

- 操作侧辊缝值历史：{data['Gap_Op']}mm
- 操作侧平均厚度偏差历史：{data['error_Op']}mm
- 操作侧的PID输出量历史：{data['out_Op']}mm
- 操作侧PID参数历史：Kp={data['Kp_Op']}, Ki={data['Ki_Op']}, Kd={data['Kd_Op']}

- 传动侧辊缝值历史：{data['Gap_Dri']}mm
- 传动侧平均厚度偏差历史：{data['error_Dri']}mm
- 传动侧的PID输出量历史：{data['out_Dri']}mm
- 传动侧PID参数历史：Kp={data['Kp_Dri']}, Ki={data['Ki_Dri']}, Kd={data['Kd_Dri']}


请基于控制理论分析并提出参数优化建议，给出一组效率和超调方面平衡的新参数组合；分析时应该注意几点：
1. 这是一个时延系统，也就意味着先大致上来说，out数组里某一位元素的控制结果在error数组里相应的后一位体现，这个结论适用于操作侧和传动侧
2. 需要考虑速度对辊压厚度响应的影响
3. 根据辊压机的相应知识，分析传动侧和操作侧的辊缝动作对厚度的影响是否具有耦合性
4. out里如果出现连续的重复值，说明下一个控制量还没有输出，注意辨别
5. 在out数组里的值之外，员工的动作也可以让辊缝发生变化，请注意辨别，分析时考虑其影响
6. 请主要观察辊缝改变量与厚度改变量的关系，out数组的值只是作为参考
7. 如果不确定，或认为不需要改变，则只需要返回字典{{"status": "0"}}，若需要改变，输出格式参考下文

直接返回如下JSON格式，直接返回字典结果，要是Python里的字典格式，不是字符串，且不要包含其他内容：
{{
  "Kp_Op": 优化后的操作侧比例系数,
  "Ki_Op": 优化后的操作侧积分系数,
  "Kd_Op": 优化后的操作侧微分系数,
  "Kp_Dri": 优化后的传动侧比例系数,
  "Ki_Dri": 优化后的传动侧积分系数,
  "Kd_Dri": 优化后的传动侧微分系数
  "status": "1"
}}"""

    try:
        response = requests.post(
            DEEPSEEK_API,
            headers={"Authorization": f"Bearer {API_KEY}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            },
            timeout=30
        )
        return response.json()['choices'][0]['message']['content']
    
    except Exception as e:
        return {"ErrorMessage": str(e)}



# 定义 CSV 文件路径（保存到桌面）
csv_file_path = os.path.join(os.path.expanduser("~"), "Desktop", "LLM_control_ignition_PIDtuner.csv")

def save_to_csv(data):

    # 检查文件是否存在
    file_exists = os.path.isfile(csv_file_path)
    
    # 打开文件并写入数据
    with open(csv_file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        
        # 如果文件不存在，写入表头
        if not file_exists:
            writer.writerow(["Timestamp", "machineNo", "Kp_Op", "Ki_Op", "Kd_Op", "Kp_Dri", "Ki_Dri", "Kd_Dri"])
        
        # 写入数据
        writer.writerow(data)


def process_data(machineNo, llm_response):

    # 生成时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 提取需要保存的数据
    data_to_save = [
        timestamp,
        machineNo,
        llm_response["Kp_Op"],
        llm_response["Ki_Op"],
        llm_response["Kd_Op"],
        llm_response["Kp_Dri"],
        llm_response["Ki_Dri"],
        llm_response["Kd_Dri"]
        ]
    
    # 保存到 CSV
    save_to_csv(data_to_save)


if __name__ == "__main__": 
    # 接收Ignition数据，从标准输入读取JSON字符串数据
    json_data = sys.stdin.read()
    
    # 反序列化JSON字符串为字典，还原输入信息
    device_data = json.loads(json_data)
    
    # 调用LLM处理，llm_response有可能是str报错代码
    # llm_response格式：格式：'```json\n{\n  "Kp_Op": 0.25,\n  "Ki_Op": 1.0,\n  "Kd_Op": 0.35,\n  "Kp_Dri": 0.25,\n  "Ki_Dri": 1.3,\n  "Kd_Dri": 0.35\n}\n```'
    start_time = time.time()
    llm_response = process_with_llm(device_data)
    
    # 使用正则表达式提取 JSON 部分
    json_str = re.search(r'\{.*\}', llm_response, re.DOTALL).group()

    # 去掉多余的换行符和空格
    json_str = json_str.replace('\n', '').replace(' ', '')

    # 解析为字典
    data_dict = json.loads(json_str)

    # 保存结果，不是每次都能有效返回
    try:
        machineNo = device_data['machineNo'][0]
        process_data(machineNo, data_dict)
    
    except:
        pass
    
    # 返回标准化结果
    print(data_dict)



    
