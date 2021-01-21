from pip._vendor import requests
import datetime
from pymongo import MongoClient
import dns
from bs4 import BeautifulSoup
import time

def save_ship_to_DB(shipData, mmsi):
    mmsi, flag, width, length, image = get_ship_data(mmsi)
    shipDataDocument = {
    "mmsi": mmsi,
    "width":width,
    "length":length,
    "flag":flag,
    "image":image}
    shipData.insert_one(shipDataDocument)
    print("Inserted:", mmsi, "to DB")


def get_ship_data(mmsi):
    site = 'https://www.vesseltracker.com/en/vessels.html?term=' + str(mmsi)
    response = requests.get(site)
    soup = BeautifulSoup(response.content, 'html.parser')
    divs = soup.findAll("div",{"class":"row odd"})
    for links in divs:
        link = links.find('a', href=True)
        ship_link = link.get('href')
    site = "https://www.vesseltracker.com" + ship_link

    response = requests.get(site)
    soup = BeautifulSoup(response.content, 'html.parser')
    vessels = {}
    tab = soup.findAll("div",{"class":"key-value-table"})
    for t in tab:
        te = t.findAll("div",{"class":"row"})
        for t in te:
            try:
                p = t.find("div",{"class":"col-xs-5 key"})
                g = t.find("div",{"class":"col-xs-7 value"})
                vessels.update( {p.string : g.string} )
            except:
                pass
    photo = soup.find("div",{"class":"detail-image"})
    images = photo.findAll('img')
    for image in images:
        ship_photo_url = ("https://" + image['src'])
        if ship_photo_url == "https:///assets/img/gen_img_ship.png":
            ship_photo_url = "https://www.vesseltracker.com/assets/img/gen_img_ship.png"
        else:
            pass
    flag = vessels["Flag:"]
    #Change Width and length "12.0 m" format to float "12.0"
    width = float(vessels["Width:"].split(" ")[0])
    length = float(vessels["Length:"].split(" ")[0])
    return mmsi, flag, width, length, ship_photo_url

def fetch_ships():
    home_coordinates = [61.058983, 28.320951]
    radius = 60  #Normal value 40km
    current_time = (datetime.datetime.utcnow() - datetime.timedelta(minutes=1)).isoformat()[:-6] + "000Z"
    api_call = "https://meri.digitraffic.fi/api/v1/locations/latitude/" + str(home_coordinates[0]) +"/longitude/" + str(home_coordinates[1]) + "/radius/" + str(radius) + "/from/" + current_time
    print(api_call)
    response = requests.get(api_call)
    ship_data = response.json()['features']
    return ship_data


client = MongoClient("mongodb+srv://mongoUser:password@mustola.g1flp.mongodb.net/ships?retryWrites=true&w=majority")
db = client.ships
shipData = db.shipDetails
mmsi_list = []

for ship in shipData.find():
    mmsi_list.append(ship['mmsi'])

while True:
    print("Fetching ships")
    ship_list = fetch_ships()
    for ship in ship_list:
        mmsi = ship['mmsi']
        
        if mmsi in mmsi_list:
            pass        
        else:
            mmsi_list.append(mmsi)
            save_ship_to_DB(shipData, mmsi)
    time.sleep(5)


