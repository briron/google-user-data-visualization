import requests
import json

with open("./etc/google_key.txt") as lf:
    API_KEY = lf.read()
    
BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json?&components=country:KR&language=ko&key=" + API_KEY + "&"


def getLatLngByAddress(address):
    url = BASE_URL + "address=" + address
    resp = requests.get(url)
    dic = json.loads(resp.text)
    lat = dic['results'][0]['geometry']['location']['lat']
    lng = dic['results'][0]['geometry']['location']['lng']
    return lat, lng


print(getLatLngByAddress("강남역"))