import numpy as np

def fspl(distance_km, frequency_ghz):
    """
    计算自由空间路径损耗 (Free Space Path Loss)
    FSPL(dB) = 20*log10(d) + 20*log10(f) + 92.45
    """
    if distance_km <= 0 or frequency_ghz <= 0:
        raise ValueError("距离和频率必须为正值")
    return 20 * np.log10(distance_km) + 20 * np.log10(frequency_ghz) + 92.45


def received_power(eirp_dbm, antenna_gain_dbi, fspl_db):
    """
    计算接收功率 (dBm)
    P_r = EIRP + G_r - FSPL
    """
    return eirp_dbm + antenna_gain_dbi - fspl_db


def link_quality(pr_dbm, threshold_dbm=-100):
    """
    根据接收功率判断链路质量
    返回: 'OK' 或 'Marginal'
    """
    return 'OK' if pr_dbm > threshold_dbm else 'Marginal'