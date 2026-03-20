# 卫星干扰检测与轨道分析工具  
**Satellite Interference Tracker**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Skyfield](https://img.shields.io/badge/Skyfield-1.0+-orange)
![License](https://img.shields.io/badge/License-MIT-green)

一款基于 Skyfield 的卫星轨道预测与干扰分析工具，支持 TLE 传播、多地面站过境计算、双星角距离干扰检测、链路预算评估，以及地面轨迹交互地图（支持中国坐标系 GCJ-02 / BD-09）。

---

- 轨道传播：NORAD TLE + SGP4 模型
- 过境预测：AOS/LOS 时间、最大仰角
- 干扰检测：同时可见时的角距离风险判断
- 链路预算：FSPL + 接收功率计算
- 可视化：仰角曲线图（PNG） + 交互式地面轨迹地图（HTML，Folium）
- 中国坐标系支持：地图显示时可转换为 GCJ-02（高德/腾讯）或 BD-09（百度）

---

## 快速开始

### 1. 安装依赖
```bash
pip install skyfield numpy pandas matplotlib folium
```

### 2. 准备输入

- **TLE 文件** → 放入 `tle_input/`  
  示例：`NOAA15.tle`、`NOAA18.tle`  
  建议从 [Celestrak](https://celestrak.org/NORAD/elements/) 下载最新（2026年3月20日已验证 NOAA 15/18 TLE 有效）

- **地面站配置** → `gs_input/gs.csv`  
  ```csv
  Name,Lat,Lon,Alt_m,Antenna_dBi,Max_TX_kW
  北京,39.9042,116.4074,44,40,20
  上海,31.2304,121.4737,4,40,20
  ```

### 3. 运行
```bash
python example_run.py
```

**输出内容**：
- 过境列表（开始/结束时间、最大仰角）
- 链路预算（接收功率、质量 OK/Marginal）
- 仰角曲线图（PNG） → `plots/北京_passes.png` 等
- 交互式地面轨迹地图（HTML） → `plots/NOAA_15_track_gcj02.html` 等（浏览器打开查看）

### 推荐参数（NOAA 系列真实配置）
在 `example_run.py` 中修改：
```python
frequency_ghz    = 1.7      # L 波段（APT/HRPT）
eirp_dbm         = 70.0     # ≈ 40 dBW
pr_threshold_dbm = -115.0   # 合理阈值
track_coord_system = 'gcj02'  # 或 'bd09'（百度坐标）或 'wgs84'
```

## 项目结构
```
Satellite-Interference-Analyzer/
├── README.md
├── requirements.txt
├── example_run.py           主脚本
├── tle_input/               TLE 文件
├── gs_input/gs.csv          地面站配置
├── satellite.py
├── groundstation.py
├── simulation.py            核心计算 + 地面轨迹
├── link_budget.py
└── plots/                   图表与地图输出
```

## 注意事项

- 过境不保证每天都有：轨道几何导致某些时段无高仰角过境，可延长 `duration_hours=72` 或调整起始时间。
- TLE 时效性：定期更新（Celestrak），当前日期 2026年3月20日 NOAA 15/18 TLE 已验证有效。
- 坐标系：核心计算使用 WGS84（国际标准），仅地图显示支持 GCJ-02/BD-09 偏移。
- 中文字体警告：若 Matplotlib 出现 Glyph missing 警告，在 `example_run.py` 添加：
  ```python
  plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
  plt.rcParams['axes.unicode_minus'] = False
  ```

## 未来扩展方向

- 多卫星星座干扰分析
- 多普勒频移 + 传播时延计算
- 轨迹颜色渐变（按仰角/日照）
- 高德/百度瓦片底图集成
- CSV/ICS 导出过境提醒

欢迎 Star、Fork 或提交 Issue/PR，一起完善！

最后更新：2026年3月20日

