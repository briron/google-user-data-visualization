import requests
import json
import folium

class GeoDataHandler:
    def __init__(self):
        with open("./etc/tmap_key.txt") as lf:
            self.__TMAP_KEY = lf.read()

        self.__DIRECTION_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"
        self.__GEOCODING_URL = "https://apis.openapi.sk.com/tmap/pois?version=1&appKey=" + self.__TMAP_KEY + "&"
        self.__REVERSE_URL = "https://apis.openapi.sk.com/tmap/geo/reversegeocoding?version=1&appKey=" + self.__TMAP_KEY + "&"

    # Singleton 패턴
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(GeoDataHandler, cls).__new__(cls)
        return cls.instance

    # 주소지를 입력하면, 위경도를 list로 반환한다.
    def getLatLngByAddress(self, address):
        url = self.__GEOCODING_URL + "searchKeyword=" + address
        resp = requests.get(url)
        dic = json.loads(resp.text)
        lat = dic['searchPoiInfo']['pois']['poi'][0]['noorLat']
        lng = dic['searchPoiInfo']['pois']['poi'][0]['noorLon']
        return lat, lng

    # 위경도를 list로 입력하면, 주소지를 str로 반환한다.
    def reverseGeocoding(self, lat_lng):
        url = self.__REVERSE_URL + "lat=" + lat_lng[0] + "&lon=" + lat_lng[1]
        resp = requests.get(url)
        dic = json.loads(resp.text)
        address = dic['addressInfo']['fullAddress']
        return address

    # Features Dictionary 에서 Coordinate 값을 추출한다.
    def getCoordinateFromFeature(self, features):
        steps = []
        for feature in features:
            if feature['geometry']['type'] == 'LineString':
                for coordinate in feature['geometry']['coordinates']:
                    steps.append(coordinate[::-1])
        return steps

    # 시작주소와 도착주소를 입력하면 도보로 이동하는 위치들을 list로 반환한다.
    def getWalkingDirectionByAddress(self, start_address, end_address):
        data = {}
        data['startName'] = start_address
        data['startY'], data['startX'] = self.getLatLngByAddress(start_address)
        data['endName'] = end_address
        data['endY'], data['endX'] = self.getLatLngByAddress(end_address)
        headers = {'appKey' : self.__TMAP_KEY}
        resp = requests.post(self.__DIRECTION_URL, headers=headers, data=data)
        dic = json.loads(resp.text)
        steps = self.getCoordinateFromFeature(dic['features'])
        return steps

    # 시작점과 도착점의 위경도를 list로 입력하면, 도보로 이동하는 위치들을 list로 반환한다.
    def getWalkingDirectionByLatLng(self, start_lat_lng, end_lat_lng):
        data = {}
        [data['startY'], data['startX']] = start_lat_lng
        [data['endY'], data['endX']] = end_lat_lng
        data['startName'] = self.reverseGeocoding(start_lat_lng)
        data['endName'] = self.reverseGeocoding(end_lat_lng)
        headers = {'appKey' : self.__TMAP_KEY}
        resp = requests.post(self.__DIRECTION_URL, headers=headers, data=data)
        dic = json.loads(resp.text)
        steps = self.getCoordinateFromFeature(dic['features'])
        return steps


class MapHandler:
    def __init__(self):
        self.m = folium.Map(location=[36, 128], zoom_start = 7)
        self.gh = GeoDataHandler()

    def initMap(self):
        self.m = folium.Map(location=[36, 128], zoom_start = 7)

    # 시작점과 도착점의 위경도를 list로 입력하여, 도보로 이동하는 것을 지도로 보여준다.
    def visualizeExpectedRouteOnFoot(self, start_lat_lng, dest_lat_lng):
        steps = self.gh.getWalkingDirectionByLatLng(start_lat_lng, dest_lat_lng)
        for i in range(len(steps) - 1):
            folium.PolyLine([steps[i], steps[i+1]], color="#00498c",weight=3.5,opacity=0.7).add_to(self.m)
        return self.m