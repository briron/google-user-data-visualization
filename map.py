import requests
import json

class GeoDataHandler:
    def __init__(self):
        with open("./tmap_key.txt") as lf:
            self.TMAP_KEY = lf.read()

        self.DIRECTION_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"
        self.GEOCODING_URL = "https://apis.openapi.sk.com/tmap/pois?version=1&appKey=" + self.TMAP_KEY + "&"
        self.REVERSE_URL = "https://apis.openapi.sk.com/tmap/geo/reversegeocoding?version=1&appKey=" + self.TMAP_KEY + "&"
    
    # 주소지를 입력하면, 위경도를 list로 반환한다.
    def getLatLngByAddress(self, address):
        url = self.GEOCODING_URL + "searchKeyword=" + address
        resp = requests.get(url)
        dic = json.loads(resp.text)
        lat = dic['searchPoiInfo']['pois']['poi'][0]['noorLat']
        lng = dic['searchPoiInfo']['pois']['poi'][0]['noorLon']
        return lat, lng

    # 위경도를 list로 입력하면, 주소지를 str로 반환한다.
    def reverseGeocoding(self, lat_lng):
        url = self.REVERSE_URL + "lat=" + lat_lng[0] + "&lon=" + lat_lng[1]
        resp = requests.get(url)
        dic = json.loads(resp.text)
        address = dic['addressInfo']['fullAddress']
        return address

    # Features Dictionary 에서 Coordinate 값을 추출한다.
    def getCoordinateFromFeature(self, features):
        steps = []
        for feature in features:
            if feature['geometry']['type'] == 'Point':
                coordinate = feature['geometry']['coordinates']
                steps.append(coordinate[::-1])
            else:
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
        headers = {'appKey' : self.TMAP_KEY}
        resp = requests.post(self.DIRECTION_URL, headers=headers, data=data)
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
        headers = {'appKey' : self.TMAP_KEY}
        resp = requests.post(self.DIRECTION_URL, headers=headers, data=data)
        dic = json.loads(resp.text)
        steps = self.getCoordinateFromFeature(dic['features'])
        return steps