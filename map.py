import requests
import json
import folium

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
        data['startName'] = self.reverseGeocoding(start_lat_lng)
        data['endName'] = self.reverseGeocoding(end_lat_lng)
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

    def initMap(self):
        self.m = folium.Map(location=[36, 128], zoom_start = 7)

    # 시작점과 도착점의 위경도를 list로 입력하여, 도보로 이동하는 것을 지도로 보여준다.
    def visualizeWalkingDirection(self, start_lat_lng, dest_lat_lng, pass_lat_lng=[]):
        steps = self.gh.getWalkingDirectionByLatLng(start_lat_lng, dest_lat_lng, pass_lat_lng)
        for i in range(len(steps) - 1):
            folium.PolyLine([steps[i], steps[i+1]], color="#00498c",weight=3.5,opacity=0.7).add_to(self.m)
        return self.m
    
    # 시작점과 도착점의 위경도를 list로 입력하여, 도보로 이동하는 것을 지도로 보여준다.
    def visualizeDrivingDirection(self, start_lat_lng, dest_lat_lng, pass_lat_lng=[]):
        steps = self.gh.getDrivingDirectionByLatLng(start_lat_lng, dest_lat_lng, pass_lat_lng)
        for i in range(len(steps) - 1):
            folium.PolyLine([steps[i], steps[i+1]], color="#00498c",weight=3.5,opacity=0.7).add_to(self.m)
        return self.m


gh = GeoDataHandler()
mh = MapHandler()
mh.visualizeDrivingDirection(list(gh.getLatLngByAddress("강남역")), list(gh.getLatLngByAddress("서울역")), [list(gh.getLatLngByAddress("명동역"))])