import requests
import json
import folium
import pandas as pd
import datetime
# from util import calcDistance
from typing import Tuple
import numpy as np

class GeoDataHandler:
    def __init__(self):
        with open("./tmap_key.txt") as lf:
            self.__TMAP_KEY = lf.read()

        self.__GEOCODING_URL = "https://apis.openapi.sk.com/tmap/pois?version=1&appKey=" + self.__TMAP_KEY + "&"
        self.__REVERSE_URL = "https://apis.openapi.sk.com/tmap/geo/reversegeocoding?version=1&appKey=" + self.__TMAP_KEY + "&"
        self.__WALKING_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"
        self.__DRIVING_URL = "https://apis.openapi.sk.com/tmap/routes?version=1"
        
    # Singleton 패턴
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GeoDataHandler, cls).__new__(cls)
        return cls.instance
    
    # 주소지를 입력하면, 위경도(str)를 tuple로 반환한다.
    def getLatLngByAddress(self, address:str) -> Tuple[str, str]:
        url = self.__GEOCODING_URL + "searchKeyword=" + address
        resp = requests.get(url)
        dic = json.loads(resp.text)
        lat = dic['searchPoiInfo']['pois']['poi'][0]['noorLat']
        lng = dic['searchPoiInfo']['pois']['poi'][0]['noorLon']
        return lat, lng

    # 위경도를 list로 입력하면, 주소지를 str로 반환한다.
    def getAddressByLatLng(self, lat_lng):
        url = self.__REVERSE_URL + "lat=" + str(lat_lng[0]) + "&lon=" + str(lat_lng[1])
        resp = requests.get(url)
        dic = json.loads(resp.text)
        address = dic['addressInfo']['fullAddress']
        return address

    # Features Dictionary 에서 Coordinate 값을 추출한다.
    def __getCoordinateFromFeature(self, features):
        steps = []
        for feature in features:
            if feature['geometry']['type'] == 'LineString':
                for coordinate in feature['geometry']['coordinates']:
                    steps.append(coordinate[::-1])
            if feature['properties']['description'] == '도착':
                break
        return steps
    
    # direction 정보를 요청하여 예상 이동경로의 위경도값을 list로 반환한다.
    def __requestDirections(self, url, data):
        headers = {'appKey' : self.__TMAP_KEY}
        resp = requests.post(url, headers=headers, data=data)
        dic = json.loads(resp.text)
        return self.__getCoordinateFromFeature(dic['features'])
    
    def __passToString(self, pass_lat_lng):
        stringList = []
        for lat_lng in pass_lat_lng:
            stringList.append(",".join(lat_lng[::-1]))
        return "_".join(stringList)
        
    # 시작주소와 도착주소, 경유주소를 입력하면, 도보로 이동하는 위치들을 list로 반환한다.
    def getWalkingDirectionByAddress(self, start_address, end_address, pass_address=[]):
        data = {}
        data['startName'] = start_address
        data['startY'], data['startX'] = self.getLatLngByAddress(start_address)
        data['endName'] = end_address
        data['endY'], data['endX'] = self.getLatLngByAddress(end_address)
        data['passList'] = self.__passToString(list(map(lambda x : list(self.getLatLngByAddress(x)), pass_address)))
        steps = self.__requestDirections(self.__WALKING_URL, data)
        return steps

    # 시작점과 도착점의 위경도를 list로 입력하면, 도보로 이동하는 위치들을 list로 반환한다.
    def getWalkingDirectionByLatLng(self, start_lat_lng, end_lat_lng, pass_lat_lng=[]):
        data = {}
        [data['startY'], data['startX']] = start_lat_lng
        [data['endY'], data['endX']] = end_lat_lng
        data['startName'] = self.getAddressByLatLng(start_lat_lng)
        data['endName'] = self.getAddressByLatLng(end_lat_lng)
        data['passList'] = self.__passToString(pass_lat_lng)
        steps = self.__requestDirections(self.__WALKING_URL, data)
        return steps
    
    # 시작주소와 도착주소를 입력하면, 차로 이동하는 위치들을 list로 반환한다.
    def getDrivingDirectionByAddress(self, start_address, end_address, pass_address=[]):
        data = {}
        data['startY'], data['startX'] = self.getLatLngByAddress(start_address)
        data['endY'], data['endX'] = self.getLatLngByAddress(end_address)
        data['passList'] = self.__passToString(list(map(lambda x : list(self.getLatLngByAddress(x)), pass_address)))
        steps = self.__requestDirections(self.__DRIVING_URL, data)
        return steps
    
    # 시작점과 도착점의 위경도를 list로 입력하면, 차로 이동하는 위치들을 list로 반환한다.
    def getDrivingDirectionByLatLng(self, start_lat_lng, end_lat_lng, pass_lat_lng=[]):
        data = {}
        [data['startY'], data['startX']] = start_lat_lng
        [data['endY'], data['endX']] = end_lat_lng
        data['passList'] = self.__passToString(pass_lat_lng)
        steps = self.__requestDirections(self.__DRIVING_URL, data)
        return steps


class MapHandler:
    def __init__(self):
        self.m = folium.Map(location=[36, 128], zoom_start = 7)
        self.gh = GeoDataHandler()

    # Singleton 패턴
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MapHandler, cls).__new__(cls)
        return cls.instance        
        
    def initMap(self):
        self.m = folium.Map(location=[36, 128], zoom_start = 7)

    # 시작점과 도착점의 위경도를 list로 입력하여, 도보로 이동하는 것을 지도로 보여준다.
    def visualizeWalkingDirection(self, start_lat_lng, dest_lat_lng, pass_lat_lng=[]):
        steps = self.gh.getWalkingDirectionByLatLng(start_lat_lng, dest_lat_lng, pass_lat_lng)
        for i in range(len(steps) - 1):
            folium.PolyLine([steps[i], steps[i+1]], color="#00498c",weight=4,opacity=0.7).add_to(self.m)
        return self.m
    
    # 시작점과 도착점의 위경도를 list로 입력하여, 도보로 이동하는 것을 지도로 보여준다.
    def visualizeDrivingDirection(self, start_lat_lng, dest_lat_lng, pass_lat_lng=[]):
        steps = self.gh.getDrivingDirectionByLatLng(start_lat_lng, dest_lat_lng, pass_lat_lng)
        for i in range(len(steps) - 1):
            folium.PolyLine([steps[i], steps[i+1]], color="#00498c",weight=4,opacity=0.7).add_to(self.m)
        return self.m
    
    def visualizeMarker(self, markers, center=pd.DataFrame(), count=10):
        self.initMap()
        if not center.empty:
            folium.Marker(center[['latitude', 'longitude']], popup=center["address"]).add_to(self.m)
        for index, row in markers.iterrows():
            folium.CircleMarker(row[['latitude', 'longitude']], radius = 8, color='#B70205', fill_color='#B70205', popup=str(row['datetime'])).add_to(self.m)
        return self.m


class LocationDataHandler:
    def __init__(self, filepath=''):
        LOCATION_FILEPATH = '../data/LocationHistory.json'
        if not filepath:
            filepath = LOCATION_FILEPATH
        with open(filepath, 'r') as lf:
            raw = json.loads(lf.read())
            self.location_data = self.preprocess(raw)
            self.calcDistance = np.vectorize(self.calcDistance)
                        
    def preprocess(self, raw):
        location_data = pd.DataFrame(raw['locations'])
        location_data = location_data[location_data.accuracy < 1000]
        location_data['latitudeE7'] = location_data['latitudeE7']/float(1e7)
        location_data['longitudeE7'] = location_data['longitudeE7']/float(1e7)
        location_data['datetime'] = location_data.timestampMs.map(lambda x: datetime.datetime.fromtimestamp((float(x)/1000), datetime.timezone(datetime.timedelta(hours=9))))
        location_data.rename(columns={'latitudeE7':'latitude', 'longitudeE7':'longitude', 'timestampMs':'timestamp'}, inplace=True)
        location_data = location_data.drop(['accuracy', 'activity', 'altitude', 'heading', 'timestamp', 'velocity', 'verticalAccuracy'], axis=1)
        location_data = location_data.sort_values(by=['datetime'])
        location_data.reset_index(drop=True, inplace=True)
        return location_data

    def calcDistance(self, lat1, lon1, lat2, lon2):
        R = 6373.0
        lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a)) 
        distance = R * c
        return distance
    
    def getNearestPlace(self, address, count=10):
        gh = GeoDataHandler()
        place_lat_lng = list(map(float,gh.getLatLngByAddress(address)))
        address = gh.getAddressByLatLng(place_lat_lng)
        # 이 부분을 수정해야 함
        center = pd.DataFrame({'latitude':place_lat_lng[0], 'longitude':place_lat_lng[1], 'address':address})
        self.location_data['distance'] = self.calcDistance(lh.location_data['latitude'], lh.location_data['longitude'], place_lat_lng[0], place_lat_lng[1])
        return center, self.location_data.iloc[self.location_data['distance'].nsmallest(10).index]
        

# 이 클래스를 완성시켜야 함
class MapService:
    def __init__(self):
        self.mh = MapHandler()
        
    def visualizeNearestPlace(self, address):
        center, markers = lh.getNearestPlace(address)
        return mh.visualizeMarker(markers, center)


gh = GeoDataHandler()
mh = MapHandler()
lh = LocationDataHandler()

#mh.visualizeMarker(lh.getNearestPlace("강남역"))
service = MapService()
service.visualizeNearestPlace("강남역")