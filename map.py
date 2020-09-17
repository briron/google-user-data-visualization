import requests
import json

with open("./google_key.txt") as lf:
    GOOGLE_KEY = lf.read()
with open("./tmap_key.txt") as lf:
    TMAP_KEY = lf.read()
    
GEOCODING_URL = "https://maps.googleapis.com/maps/api/geocode/json?components=country:KR&language=ko&key=" + GOOGLE_KEY + "&"
DIRECTION_URL = "https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1"

def getLatLngByAddress(address):
    url = GEOCODING_URL + "address=" + address
    resp = requests.get(url)
    dic = json.loads(resp.text)
    lat = dic['results'][0]['geometry']['location']['lat']
    lng = dic['results'][0]['geometry']['location']['lng']
    return lat, lng

def getWalkingDirectionByAddress(start_address, end_address):
    data = {}
    data['startName'] = start_address
    data['startY'], data['startX'] = getLatLngByAddress(start_address)
    data['endName'] = end_address
    data['endY'], data['endX'] = getLatLngByAddress(end_address)
    headers = {'appKey' : TMAP_KEY}
    resp = requests.post(DIRECTION_URL, headers=headers, data=data)
    dic = json.loads(resp.text)
    print(dic)

print(getLatLngByAddress("강남역"))
