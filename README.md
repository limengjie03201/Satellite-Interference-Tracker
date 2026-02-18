# 卫星干扰检测与轨道分析工具  
**Satellite Interference Tracker**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Skyfield](https://img.shields.io/badge/Skyfield-1.0+-orange)

一款基于 Python 的卫星轨道预测与干扰检测工具，使用 Skyfield 库实现 TLE 轨道传播，支持多地面站的可视过境预测、两颗卫星间角距离干扰检测，以及基本的链路预算分析。

适用于航天工程学习、卫星通信协调演示、面试项目展示等场景。

## 项目特点

- **轨道传播**：基于 NORAD TLE + SGP4 模型，精确预测卫星位置
- **过境预测**：计算地面站上卫星的 AOS/LOS 时间、最大仰角
- **干扰检测**：当两颗卫星同时可见且角距离小于阈值时标记干扰风险
- **链路预算**：计算自由空间路径损耗 (FSPL) 与接收功率，评估链路质量
- **可视化**：生成仰角-时间曲线图，并在干扰窗口处高亮显示
- **中英双语注释**：代码注释采用中英结合，便于学习与分享

## 适用场景

- 学习航天轨道力学、卫星通信基础
- 模拟 LEO 卫星（如 NOAA 系列）对特定地面站的可见性
- 演示卫星间潜在同频干扰（ITU 协调相关概念）
- 航天/卫星通信方向的简历项目或技术分享

## 安装与依赖

### 环境要求
- Python 3.10 或更高版本

### 安装依赖
```bash
pip install -r requirements.txt
```

```
skyfield
numpy
pandas
matplotlib
```

1. **准备 TLE 文件**  
   从 [Celestrak](https://celestrak.org/NORAD/elements/) 下载最新 TLE，例如 NOAA 15 / NOAA 18，保存到 `tle_input/` 目录。

**配置地面站**  
   编辑 `gs_input/gs.csv`，示例格式：
   ```csv
   Name,Lat,Lon,Alt_m,Antenna_dBi,Max_TX_kW
   北京,39.9042,116.4074,44,40,20
   上海,31.2304,121.4737,4,40,20
   ```

2. 准备输入文件

TLE 文件：放入 tle_input/ 目录
示例文件名：NOAA15.tle、NOAA18.tle
可从 Celestrak 获取最新 TLE
地面站配置文件：gs_input/gs.csv
示例内容：

3. 运行示例
```
python example_run.py
```

运行后将输出：

- 每个地面站的过境列表（开始/结束时间、最大仰角）
- 链路预算结果（最小接收功率、质量评估）
- 潜在干扰风险提示（若存在）
- 仰角曲线图自动保存至 plots/ 目录

### 推荐参数（针对 NOAA 系列天气卫星）

NOAA 15/18 的主要下行链路为 L 波段（~1.7 GHz），建议在 example_run.py 中设置更真实的参数：
```
frequency_ghz    = 1.7      # NOAA APT/HRPT 常用频率
eirp_dbm         = 70.0     # ≈ 40 dBW，典型卫星等效全向辐射功率
pr_threshold_dbm = -115.0   # 更合理的接收功率阈值
```

### 项目结构说明
```
Satellite-Interference-Analyzer/
├── README.md                本说明文件
├── requirements.txt
├── example_run.py           主运行脚本（示例）
├── tle_input/               TLE 文件目录
│   ├── NOAA15.tle
│   └── NOAA18.tle
├── gs_input/
│   └── gs.csv               地面站列表
├── satellite.py             卫星类
├── groundstation.py         地面站类
├── simulation.py            核心计算（过境、干扰、链路预算）
├── link_budget.py           链路预算计算模块
└── plots/                   自动生成的图表保存目录
```

## 注意事项

过境并非每天都有
受轨道倾角、升交点赤经漂移及地面站纬度影响，某些日期/地点 24 小时内可能无高仰角过境。
建议：延长模拟时长（duration_hours=72 或 96）或调整起始时间。
TLE 时效性
TLE 精度随时间快速下降，请定期从 Celestrak 更新。
链路预算简化模型
当前仅考虑自由空间损耗，未包含大气衰减、雨衰、天线指向误差、噪声温度等因素。
坐标系
全部使用 WGS84 坐标系，与国际卫星标准一致。

### 未来可扩展方向

支持多颗卫星（星座级）干扰分析
加入多普勒频移、传播时延计算
集成真实天线方向图与旁瓣电平干扰模型
添加 3D 轨道/地面轨迹可视化（Plotly / Cesium）
支持用户通过配置文件自定义频率、EIRP、噪声系数等

### 致谢

Skyfield — 强大且优雅的 Python 天文/轨道计算库
Celestrak — 提供免费、可靠的公开 TLE 数据
NOAA 系列卫星 — 经典的低轨气象卫星示例

欢迎 Star、Fork 或提交 Issue/PR，一起完善这个航天学习工具！