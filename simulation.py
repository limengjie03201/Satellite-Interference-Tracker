from skyfield.api import load
import numpy as np
import datetime as dt
from link_budget import fspl, received_power, link_quality

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
        # 计算卫星相对于地面站的视线向量
        difference = satellite.sat - gs.location
        topocentric = difference.at(t)
        alt, az, dist = topocentric.altaz()
        elevations.append(alt.degrees)
        distances.append(dist.km)
    
    # 检测可视区间 (elevation > threshold)
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
    
    if start_idx is not None:  # 处理跨越结束时间的过境
        passes.append((times[start_idx], times[-1], max_elev))
    
    return passes, times, elevations, distances


def compute_interference(sat1, sat2, gs, times, elev1, elev2, sep_threshold=2.0, elev_threshold=5.0):
    """
    检测两颗卫星同时可见且角距离过近的干扰窗口
    返回: [(时间, 角距离), ...]
    """
    interference_windows = []
    for i, t in enumerate(times):
        # 两颗卫星都高于最小仰角才考虑
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
        
        if not pr_values:
            min_pr = -np.inf
            quality = 'Marginal'
        else:
            min_pr = min(pr_values)
            quality = link_quality(min_pr, pr_threshold_dbm)
        
        link_budgets.append((start_t, min_pr, quality))
    
    return link_budgets