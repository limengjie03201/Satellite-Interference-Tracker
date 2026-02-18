from skyfield.api import EarthSatellite

class Satellite:
    """
    卫星类 - Satellite class
    从 TLE 文件加载卫星轨道信息
    """
    def __init__(self, tle_file):
        try:
            with open(tle_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            if len(lines) < 3:
                raise ValueError(f"TLE 文件格式错误: {tle_file}")
            
            self.name = lines[0].strip()
            # 使用 Skyfield 的 EarthSatellite 对象加载 TLE
            self.sat = EarthSatellite(lines[1].strip(), lines[2].strip(), self.name)
        except FileNotFoundError:
            raise FileNotFoundError(f"找不到 TLE 文件: {tle_file}")
        except Exception as e:
            raise RuntimeError(f"加载 TLE 失败: {e}")

    def get_position(self, ts):
        """获取指定时刻的卫星位置 / Get satellite position at given time"""
        return self.sat.at(ts)