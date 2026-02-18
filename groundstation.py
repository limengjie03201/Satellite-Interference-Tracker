from skyfield.api import Topos

class GroundStation:
    """
    地面站类 - Ground station class
    用于存储地面站的位置信息（WGS84坐标）
    """
    def __init__(self, name, lat, lon, alt_m):
        self.name = name                    # 站名 / Station name
        self.lat = lat                      # 纬度 (度) / Latitude in degrees
        self.lon = lon                      # 经度 (度) / Longitude in degrees
        self.alt_m = alt_m                  # 海拔高度 (米) / Altitude in meters
        # 创建 Skyfield 的 Topos 对象，用于后续视线计算
        self.location = Topos(latitude_degrees=lat, longitude_degrees=lon, elevation_m=alt_m)