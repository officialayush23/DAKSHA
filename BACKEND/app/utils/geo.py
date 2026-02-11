# app/utils/geo.py
# app/utils/geo.py
from geoalchemy2.shape import to_shape
from shapely.geometry import Point

def serialize_point(point_obj):
    # Converts DB WKBElement to [lon, lat] list
    if point_obj is None: 
        return None
    try:
        shape = to_shape(point_obj)
        return [shape.x, shape.y]
    except:
        return None