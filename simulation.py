from skyfield.api import load
import numpy as np
import datetime as dt
from link_budget import fspl, received_power, link_quality
import folium
import math

# 坐标转换函数（WGS84 → GCJ-02 / BD-09）

def out_of_china(lng, lat):
    """粗略判断是否在中国大陆境外"""
    return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)

def transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * math.pi) + 40.0 * math.sin(y / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * math.pi) + 320.0 * math.sin(y * math.pi / 30.0)) * 2.0 / 3.0
    return ret

def transform_lon(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * math.pi) + 20.0 * math.sin(2.0 * x * math.pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * math.pi) + 40.0 * math.sin(x / 3.0 * math.pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * math.pi) + 300.0 * math.sin(x / 30.0 * math.pi)) * 2.0 / 3.0
    return ret

def wgs84_to_gcj02(lng, lat):
    """WGS84 → GCJ-02（火星坐标，高德/腾讯等）"""
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transform_lat(lng - 105.0, lat - 35.0)
    dlng = transform_lon(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * math.pi
    magic = math.sin(radlat)
    magic = 1 - 0.00669342162296594323 * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((6378245.0 * magic) / sqrtmagic * math.pi)
    dlng = (dlng * 180.0) / (6378245.0 / sqrtmagic * math.cos(radlat) * math.pi)
    return lng + dlng, lat + dlat

def wgs84_to_bd09(lng, lat):
    """WGS84 → BD-09（百度坐标）"""
    lng_gcj, lat_gcj = wgs84_to_gcj02(lng, lat)
    if out_of_china(lng_gcj, lat_gcj):
        return lng_gcj, lat_gcj
    x = lng_gcj
    y = lat_gcj
    z = math.sqrt(x * x + y * y) + 0.00002 * math.sin(y * math.pi)
    theta = math.atan2(y, x) + 0.000003 * math.cos(x * math.pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return bd_lng, bd_lat


def compute_passes(satellite, gs, duration_hours=24, timestep_sec=60, elev_threshold=5.0):
    """
    计算卫星对某地面站的可视过境 (passes)
    返回: passes列表, 时间数组, 仰角数组, 距离数组(km)
    """
    ts = load.timescale()
    t0 = ts.now()
    start_dt = t0.utc_datetime().replace(microsecond=0)
    end_dt = start_dt + dt.timedelta(hours=duration_hours)
    
    num_steps = int((end_dt - start_dt).total_seconds() / timestep_sec) + 1
    dt_list = [start_dt + dt.timedelta(seconds=i * timestep_sec) for i in range(num_steps)]
    times = ts.from_datetimes(dt_list)
    
    elevations = []
    distances = []
    for t in times:
        difference = satellite.sat - gs.location
        topocentric = difference.at(t)
        alt, az, dist = topocentric.altaz()
        elevations.append(alt.degrees)
        distances.append(dist.km)
    
    visible = np.array(elevations) > elev_threshold
    passes = []
    start_idx = None
    max_elev = -np.inf
    
    for i, v in enumerate(visible):
        if v:
            if start_idx is None:
                start_idx = i
                max_elev = elevations[i]
            max_elev = max(max_elev, elevations[i])
        elif start_idx is not None:
            passes.append((times[start_idx], times[i-1], max_elev))
            start_idx = None
            max_elev = -np.inf
    
    if start_idx is not None:
        passes.append((times[start_idx], times[-1], max_elev))
    
    return passes, times, elevations, distances


def compute_interference(sat1, sat2, gs, times, elev1, elev2, sep_threshold=2.0, elev_threshold=5.0):
    """
    检测两颗卫星同时可见且角距离过近的干扰窗口
    """
    interference_windows = []
    for i, t in enumerate(times):
        if elev1[i] > elev_threshold and elev2[i] > elev_threshold:
            topo1 = (sat1.sat - gs.location).at(t)
            topo2 = (sat2.sat - gs.location).at(t)
            separation = topo1.separation_from(topo2).degrees
            if separation < sep_threshold:
                interference_windows.append((t, separation))
    return interference_windows


def compute_link_budget_for_passes(passes, times, distances, frequency_ghz, eirp_dbm, antenna_gain_dbi, pr_threshold_dbm=-100):
    """
    为每个过境计算链路预算（取过境期间最小接收功率）
    """
    link_budgets = []
    times_dt = np.array([t.utc_datetime() for t in times])
    
    for start_t, end_t, _ in passes:
        start_dt = start_t.utc_datetime()
        end_dt   = end_t.utc_datetime()
        mask = (times_dt >= start_dt) & (times_dt <= end_dt)
        
        if not np.any(mask):
            continue
        
        pass_distances = np.array(distances)[mask]
        
        pr_values = []
        for d in pass_distances:
            if d <= 0: continue
            fspl_db = fspl(d, frequency_ghz)
            pr_dbm = received_power(eirp_dbm, antenna_gain_dbi, fspl_db)
            pr_values.append(pr_dbm)
        
        min_pr = min(pr_values) if pr_values else -np.inf
        quality = link_quality(min_pr, pr_threshold_dbm)
        link_budgets.append((start_t, min_pr, quality))
    
    return link_budgets



def interactive_ground_track(satellite, gs, times, coord_system='gcj02'):
    """
    生成卫星地面轨迹交互地图，支持 WGS84 / GCJ-02 / BD-09
    coord_system: 'wgs84' / 'gcj02' / 'bd09'
    """
    gs_lat, gs_lon = gs.lat, gs.lon
    if coord_system == 'gcj02':
        gs_lon, gs_lat = wgs84_to_gcj02(gs_lon, gs_lat)
        map_title = f"{satellite.name} 地面轨迹 (GCJ-02)"
    elif coord_system == 'bd09':
        gs_lon, gs_lat = wgs84_to_bd09(gs_lon, gs_lat)
        map_title = f"{satellite.name} 地面轨迹 (BD-09)"
    else:
        map_title = f"{satellite.name} 地面轨迹 (WGS84)"

    m = folium.Map(location=[gs_lat, gs_lon], zoom_start=5, tiles='CartoDB positron')

    points = []
    for t in times:
        sub = satellite.sat.at(t).subpoint()
        lat = sub.latitude.degrees
        lon = sub.longitude.degrees

        if coord_system == 'gcj02':
            lon, lat = wgs84_to_gcj02(lon, lat)
        elif coord_system == 'bd09':
            lon, lat = wgs84_to_bd09(lon, lat)

        points.append((lat, lon))

    folium.PolyLine(points, color="blue", weight=2.5, opacity=0.8,
                    tooltip=map_title).add_to(m)

    folium.Marker([gs_lat, gs_lon],
                  popup=f"{gs.name}<br>Lat: {gs_lat:.4f}°<br>Lon: {gs_lon:.4f}° ({coord_system.upper()})",
                  icon=folium.Icon(color="red", icon="info-sign")).add_to(m)

    output_file = f"plots/{satellite.name.replace(' ', '_')}_track_{coord_system}.html"
    m.save(output_file)
    print(f"{coord_system.upper()} 地面轨迹地图已保存：{output_file}")