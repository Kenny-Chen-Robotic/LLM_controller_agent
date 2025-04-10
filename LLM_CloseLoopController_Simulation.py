"""
非线性阀门控制仿真系统
- 对比LLM直接控制与PID算法
- 包含非线性热力学模型和随机扰动
- 输出连续阀门开度（0-100%）
"""

import numpy as np
import matplotlib.pyplot as plt
import requests
from scipy.integrate import odeint
from sklearn.metrics import mean_squared_error
import time

# DeepSeek API配置
DEEPSEEK_API_KEY = YOUR-KEY
API_URL = "https://api.deepseek.com/v1/chat/completions"


# ======================
# 系统参数配置
# ======================
T_ENV = 25.0    # 环境温度(℃)
T_TARGET = 50.0 # 目标温度(℃)
C = 2000        # 热容(J/(kg·℃))
DT = 1          # 控制周期(s)
SIM_TIME = 60  # 总仿真步长

# 非线性参数
K_NL = 0.002    # 非线性热传导系数
NOISE_STD = 0.5 # 温度噪声标准差

# ======================
# 热力学系统模型
# ======================

class ThermalSystem:
    def __init__(self):
        self.temp = T_ENV
        self.time = 0
        
    def update(self, valve, dt):
        effective_power = 200 * valve * (1 - 0.8*(valve/100 - 0.5))**2
        dT = (effective_power - 50*(self.temp - T_ENV) - K_NL*(self.temp - T_ENV)**2) / C
        noise = np.random.normal(0, NOISE_STD)
        self.temp += dT * dt + noise
        self.time += dt
        return self.temp

# ======================
# 控制器实现
# ======================
class LLMController:

    def __init__(self):
        self.history = []  # 温度历史记录
        
    def get_valve(self, current_temp, target_temp):
        # 构建提示词
        prompt = f"""
你是一名过程控制的专家，当前完成一项过程控制任务，控制系统具有非线性，请应用闭环控制方面的知识，提供建议的阀门开度，让温度保持在目标温度附近
计算时可采用混合控制策略，根据数据情况自行判断，包括但不限于PID算法
当前温度：{current_temp:.1f}℃
目标温度：{target_temp}℃
历史趋势：{self._format_history()}

请根据控制理论输出阀门开度（0-100%）：
1. 当温差>10℃时全开（100%）
2. 需抑制超调和振荡
3. 可以输出0值，代表关闭阀门
4. 可输出小数
请直接输出数字（例如2.6），不要包含其他文本。"""


        # API调用
        try:
            """ 调用DeepSeek获取控制决策 """
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                    "role": "user",
                    "content": prompt
                    }],
            }

            response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
            valve = float(response.json()['choices'][0]['message']['content'])
            print(f"""
                    === 控制周期调试信息 ===
                    
                    API原始响应：
                    {response.text}
                    
                    解析结果：{valve}%
                    历史趋势：{self.history[-3:]}
                    """)
                    
            return np.clip(valve, 0, 100)
        
        except Exception as e:
            print(f"控制异常: {str(e)}")
            return 0  # 安全模式，返回开度0

    def _format_history(self):
        """格式化最近3次温度记录"""
        if len(self.history) < 3:
            return "无历史记录"
        return " → ".join(f"{t:.1f}℃" for t in self.history[-3:])

class PIDController:
    """PID控制器"""
    def __init__(self, Kp=8, Ki=0.1, Kd=2):
        self.Kp = Kp    # 比例系数
        self.Ki = Ki    # 积分系数
        self.Kd = Kd    # 微分系数
        self.integral = 0  # 积分项
        self.prev_error = 0  # 上一时刻误差
        
    def get_valve(self, current_temp, target_temp): 
        """计算PID控制量"""
        error = target_temp - current_temp
        
        # 积分项防饱和
        if abs(error) < 2:
            self.integral += error * DT
        else:
            self.integral = 0
            
        # 微分项
        derivative = (error - self.prev_error) / DT
        
        # PID计算
        output = (self.Kp * error 
                + self.Ki * self.integral 
                + self.Kd * derivative)
        
        self.prev_error = error
        return np.clip(output, 0, 100)

# ======================
# 仿真测试
# ======================
def simulate(controller):
    """运行控制仿真"""
    system = ThermalSystem()
    temps, valves, times, targets = [], [], [], []  # 新增targets记录
    last_valve = 0
    
    for step in range(int(SIM_TIME/DT)):
        # 动态目标温度设置（40秒时从50变到70）
        current_target = 70 if system.time >= 40 else 50  # !!! 关键修改
        
        # 传递当前目标给控制器
        valve = controller.get_valve(system.temp, current_target)  # !!! 修改接口
        system.update(valve, DT)
        last_valve = valve
        
        # 记录数据
        temps.append(system.temp)
        valves.append(valve)
        times.append(system.time)
        targets.append(current_target)  # 记录目标序列
        
        if isinstance(controller, LLMController):
            controller.history.append(system.temp)
            
    return times, temps, valves, targets  # 返回目标序列

# ======================
# 结果分析与可视化
# ======================
def evaluate(times, temps, valves, label):
    """评估控制性能"""
    rmse = np.sqrt(mean_squared_error([T_TARGET]*len(temps), temps))
    avg_valve = np.mean(valves)
    return {
        "label": label,
        "rmse": rmse,
        "avg_valve": avg_valve,
        "temps": temps,
        "valves": valves,
        "times": times
    }

start = time.time()
# 运行仿真时获取目标序列
llm_times, llm_temps, llm_valves, targets = simulate(LLMController())
pid_times, pid_temps, pid_valves, _ = simulate(PIDController())

# 绘制动态目标线
plt.figure(figsize=(12, 6))
plt.plot(llm_times, llm_temps, 'r-', label='Deepseek')
plt.plot(pid_times, pid_temps, 'b--', label='PID controller')
plt.step([0,40,40,60], [50,50,70,70], 'g--', where='post', label='Target')  # !!! 阶梯变化
plt.ylabel('Temperature(℃)')
plt.title('Nonlinear System Control')
plt.legend()

# 绘制阀门开度
plt.figure(figsize=(12, 6))
plt.plot(llm_times, llm_valves, 'r-', label='Deepseek')
plt.plot(pid_times, pid_valves, 'b--', label='PID controller')
plt.ylabel('valve (%)')
plt.ylim(0, 105)
plt.title('Control Signal Comparision')
plt.legend()

plt.tight_layout()
plt.show()



print('总耗时： ', time.time()-start)


