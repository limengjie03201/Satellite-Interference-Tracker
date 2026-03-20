import os
import pandas as pd
import matplotlib.pyplot as plt
from satellite import Satellite
from groundstation import GroundStation
from simulation import compute_passes, compute_interference, compute_link_budget_for_passes, interactive_ground_track
from skyfield.api import load

os.makedirs('plots', exist_ok=True)

elev_threshold = 5.0          # 最小可视仰角 (度)
sep_threshold = 2.0           # 干扰判断角距离阈值 (度)
frequency_ghz = 1.7           # NOAA 常用 L 波段
eirp_dbm = 70.0               # ≈ 40 dBW
pr_threshold_dbm = -115.0     # 更合理的接收功率阈值

visualize_tracks = True
track_coord_system = 'gcj02'  # 'wgs84' / 'gcj02' / 'bd09'

try:
    sat1 = Satellite('tle_input/NOAA15.tle')
    sat2 = Satellite('tle_input/NOAA18.tle')
    sats = [sat1, sat2]
except Exception as e:
    print(f"加载卫星失败: {e}")
    exit(1)

try:
    gs_df = pd.read_csv('gs_input/gs.csv')
    gs_list = []
    for _, row in gs_df.iterrows():
        gs = GroundStation(row['Name'], row['Lat'], row['Lon'], row['Alt_m'])
        gs.antenna_gain_dbi = row['Antenna_dBi']
        gs_list.append(gs)
except Exception as e:
    print(f"加载地面站数据失败: {e}")
    exit(1)

ts = load.timescale()

def print_results(gs, sats, elev_threshold, sep_threshold, frequency_ghz, eirp_dbm, pr_threshold_dbm):
    print(f"\n地面站: {gs.name} / Ground Station: {gs.name}")
    
    pass_data = {}
    distances_data = {}
    for sat in sats:
        passes, times, elevs, dists = compute_passes(sat, gs, elev_threshold=elev_threshold)
        pass_data[sat.name] = (passes, times, elevs)
        distances_data[sat.name] = dists
        
        print(f"卫星: {sat.name}")
        pass_df = pd.DataFrame(
            [(p[0].utc_datetime(), p[1].utc_datetime(), f"{p[2]:.1f}") for p in passes],
            columns=['开始时间', '结束时间', '最大仰角(°)']
        )
        print(pass_df.to_string(index=False))
        
        link_budgets = compute_link_budget_for_passes(
            passes, times, dists, frequency_ghz, eirp_dbm, gs.antenna_gain_dbi, pr_threshold_dbm
        )
        link_df = pd.DataFrame(
            [(lb[0].utc_datetime(), f"{lb[1]:.1f}", lb[2]) for lb in link_budgets],
            columns=['过境开始', '最小接收功率(dBm)', '质量']
        )
        print("\n链路预算 / Link Budgets:")
        print(link_df.to_string(index=False))

def plot_passes(gs, sats, elev_threshold, sep_threshold):
    plt.figure(figsize=(12, 6))
    
    pass_data = {}
    for sat in sats:
        _, times, elevs, _ = compute_passes(sat, gs, elev_threshold=elev_threshold)
        times_dt = [t.utc_datetime() for t in times]
        pass_data[sat.name] = (times_dt, elevs)
        plt.plot(times_dt, elevs, label=sat.name)
    
    times_dt = pass_data[sats[0].name][0]
    elev1 = pass_data[sats[0].name][1]
    elev2 = pass_data[sats[1].name][1]
    
    shading_regions = []
    in_region = False
    start_time = None
    for i, t_dt in enumerate(times_dt):
        t_sf = ts.from_datetime(t_dt)
        topo1 = (sats[0].sat - gs.location).at(t_sf)
        topo2 = (sats[1].sat - gs.location).at(t_sf)
        separation = topo1.separation_from(topo2).degrees
        
        if elev1[i] > elev_threshold and elev2[i] > elev_threshold and separation < sep_threshold:
            if not in_region:
                start_time = t_dt
                in_region = True
        else:
            if in_region:
                end_time = times_dt[i-1]
                shading_regions.append((start_time, end_time))
                in_region = False
    if in_region:
        shading_regions.append((start_time, times_dt[-1]))
    
    for start, end in shading_regions:
        plt.axvspan(start, end, color='red', alpha=0.3, label='Interference Risk' if not plt.gca().get_legend_handles_labels()[1] else "")
    
    plt.title(f"{gs.name} 上空的卫星过境")
    plt.xlabel("UTC 时间")
    plt.ylabel("仰角 (度)")
    plt.grid(True)
    plt.ylim(0, 90)
    plt.legend()
    plt.tight_layout()
    plot_file = f"plots/{gs.name.replace(' ', '_')}_passes.png"
    plt.savefig(plot_file)
    print(f"仰角曲线图已保存至: {plot_file}")
    plt.close()

for gs in gs_list:
    print_results(gs, sats, elev_threshold, sep_threshold, frequency_ghz, eirp_dbm, pr_threshold_dbm)
    plot_passes(gs, sats, elev_threshold, sep_threshold)
    
    if visualize_tracks:
        print(f"\n生成 {gs.name} 地面站的卫星轨迹图（坐标系: {track_coord_system.upper()}）...")
        for sat in sats:
            _, times, _, _ = compute_passes(sat, gs, duration_hours=24, timestep_sec=60, elev_threshold=elev_threshold)
            interactive_ground_track(sat, gs, times, coord_system=track_coord_system)