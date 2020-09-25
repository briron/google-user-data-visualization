import requests
import json
import folium
from folium.plugins import HeatMap
import pandas as pd
import datetime
from typing import Tuple, List
import numpy as np

class GeoDataHandler:
    def __init__(self):
        with open("./etc/tmap_key.txt") as lf:
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
    def getWalkingDirectionByLatLng(self, start_lat_lng : List[float], end_lat_lng: List[float], pass_lat_lng=[]):
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
    def getDrivingDirectionByLatLng(self, start_lat_lng : List[float], end_lat_lng: List[float], pass_lat_lng=[]):
        data = {}
        [data['startY'], data['startX']] = start_lat_lng
        [data['endY'], data['endX']] = end_lat_lng
        data['passList'] = self.__passToString(pass_lat_lng)
        steps = self.__requestDirections(self.__DRIVING_URL, data)
        return steps


class MapHandler:
    def __init__(self):
        self.m = folium.Map(location=[36, 128], zoom_start = 7)

    # Singleton 패턴
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(MapHandler, cls).__new__(cls)
        return cls.instance        
        
    def initMap(self):
        self.m = folium.Map(location=[36, 128], zoom_start = 7)
        return self.m
        
    def visualizePolyLine(self, steps):
        for i in range(len(steps) - 1):
            folium.PolyLine([steps[i], steps[i+1]], color="#00498c",weight=4,opacity=0.7).add_to(self.m)
        return self.m
  
    def visualizeMarker(self, markers, center={}, count=10):
        if center:
            folium.Marker([center['latitude'], center['longitude']], popup=center['address']).add_to(self.m)
        for index, row in markers.iterrows():
            folium.CircleMarker(row[['latitude', 'longitude']], radius = 8, color='#B70205', fill_color='#B70205', popup=str(row['datetime'])).add_to(self.m)
        return self.m
    
    def visualizeHeatmap(self, location):
        heatmap_data = np.concatenate((location.values, np.ones((len(location.values), 1)) * 0.2), axis=1)
        HeatMap(heatmap_data).add_to(self.m)
        return self.m


class LocationDataHandler:
    def __init__(self, filepath='', fp=None):
        self.__calcDistance = np.vectorize(self.__calcDistance)
        if not fp:
            if not filepath:
                LOCATION_FILEPATH = '../data/LocationHistory.json'
                filepath = LOCATION_FILEPATH
            fp = open(filepath, 'r')
        raw = json.loads(fp.read())
        self.location_data = self.preprocess(raw)
            
    def preprocess(self, raw):
        location_data = pd.DataFrame(raw['locations'])
        location_data = location_data[location_data.accuracy < 1000]
        location_data['latitudeE7'] = location_data['latitudeE7']/float(1e7)
        location_data['longitudeE7'] = location_data['longitudeE7']/float(1e7)
        location_data['timestampMs'] = location_data['timestampMs'].map(lambda x: ((float(x)/1000)))
        location_data['datetime'] = location_data.timestampMs.map(lambda x: datetime.datetime.fromtimestamp(x, datetime.timezone(datetime.timedelta(hours=9))))
        location_data.rename(columns={'latitudeE7':'latitude', 'longitudeE7':'longitude'}, inplace=True)
        location_data = location_data.drop(['accuracy', 'activity', 'altitude', 'heading', 'timestampMs', 'velocity', 'verticalAccuracy'], axis=1)
        location_data = location_data.sort_values(by=['datetime'])
        location_data.reset_index(drop=True, inplace=True)
        return location_data

    def __calcDistance(self, lat1, lon1, lat2, lon2):
        R = 6373.0
        lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a)) 
        distance = R * c
        return distance
    
    def getNearestLocation(self, address, count=10) -> Tuple[dict, pd.DataFrame]:
        gh = GeoDataHandler()
        place_lat_lng = list(map(float,gh.getLatLngByAddress(address)))
        address = gh.getAddressByLatLng(place_lat_lng)
        center = {'latitude':float(place_lat_lng[0]), 'longitude':float(place_lat_lng[1]), 'address':address}
        self.location_data['distance'] = self.__calcDistance(self.location_data['latitude'], self.location_data['longitude'], place_lat_lng[0], place_lat_lng[1])
        nearest_location = self.location_data.iloc[self.location_data['distance'].nsmallest(count).index]
        self.location_data = self.location_data.drop('distance', axis=1)
        return center, nearest_location
    
    def getTimeLocation(self, from_time, to_time):
        return self.location_data[(self.location_data.datetime >= from_time) & (self.location_data.datetime <= to_time)]
    
    def getPassLatLng(self, time_location, passCount):
        pass_lat_lng = []
        passCount = min(5, max(0, passCount))
        for i in range(passCount):
            idx = int(time_location.count() * i / passCount)
            pass_lat_lng.append(time_location.iloc[idx][['latitude', 'longitude']].tolist())
        return pass_lat_lng
        

class MapService:
    def __init__(self, lh):
        self.lh = lh
        self.mh = MapHandler()
        self.gh = GeoDataHandler()
        
    def visualizeNearestLocation(self, address):
        self.mh.initMap()
        center, markers = self.lh.getNearestLocation(address)
        return self.mh.visualizeMarker(markers, center=center)
    
    def visualizeTimeLocation(self, from_time, to_time):
        self.mh.initMap()
        time_location = self.lh.getTimeLocation(from_time, to_time)
        return self.mh.visualizeMarker(time_location)
    
    def visualizeWalkingDirection(self, from_time, to_time, passCount=0):
        self.mh.initMap()
        time_location = self.lh.getTimeLocation(from_time, to_time)
        if len(time_location) <= 1:
            return self.mh.initMap()
        start_lat_lng = time_location.iloc[0][['latitude', 'longitude']].tolist()
        dest_lat_lng = time_location.iloc[-1][['latitude', 'longitude']].tolist()
        pass_lat_lng = lh.getPassLatLng(time_location, passCount)
        steps = self.gh.getWalkingDirectionByLatLng(start_lat_lng, dest_lat_lng, pass_lat_lng)
        self.mh.visualizeMarker(time_location)
        return self.mh.visualizePolyLine(steps)
    
    def visualizeDrivingDirection(self, from_time, to_time, passCount=0):
        self.mh.initMap()
        time_location = self.lh.getTimeLocation(from_time, to_time)
        if len(time_location) <= 1:
            return self.mh.initMap()
        start_lat_lng = time_location.iloc[0][['latitude', 'longitude']].tolist()
        dest_lat_lng = time_location.iloc[-1][['latitude', 'longitude']].tolist()
        pass_lat_lng = lh.getPassLatLng(time_location, passCount)
        steps = self.gh.getDrivingDirectionByLatLng(start_lat_lng, dest_lat_lng, pass_lat_lng)
        self.mh.visualizeMarker(time_location)
        return self.mh.visualizePolyLine(steps)
    
    def visualizeTimeHeatmap(self, from_time, to_time):
        self.mh.initMap()
        time_location = self.lh.getTimeLocation(from_time, to_time)
        time_location = time_location.drop('datetime', axis=1)
        return self.mh.visualizeHeatmap(time_location)


if __name__ == "__main__":
    gh = GeoDataHandler()
    mh = MapHandler()
    lh = LocationDataHandler()
    service = MapService(lh)