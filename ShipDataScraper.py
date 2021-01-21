from pip._vendor import requests
import datetime
from pymongo import MongoClient
import dns
from bs4 import BeautifulSoup
import time
import firebase_admin
from firebase_admin import credentials, firestore

def save_ship_to_DB(mmsi):
    mmsi, flag, width, length, image = get_ship_data(mmsi)
    
    firestore_db.collection(u'ships').add({
    "mmsi": mmsi,
    "width":width,
    "length":length,
    "flag":flag,
    "image":image})
    
    print("Inserted:", mmsi, "to DB")


#Scrapes extra ship data from 3rd party website. Used only if data is not found in DB.
def get_ship_data(mmsi):
    #If imo not found, uses mmsi to find ships page
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

cred = credentials.Certificate("/home/pi/Desktop/serviceAccountKey.json")
print(cred)

firebase_admin.initialize_app(cred)
firestore_db = firestore.client()

mmsi_list = []

ships = list(firestore_db.collection(u'ships').get())
for snapshot in ships:
    ship = snapshot.to_dict()
    mmsi_list.append(ship['mmsi'])
print(mmsi_list)

while True:
    print("Fetching ships")
    ship_list = fetch_ships()
    for ship in ship_list:
        mmsi = ship['mmsi']
        
        if mmsi in mmsi_list:
            pass        
        else:
            mmsi_list.append(mmsi)
            save_ship_to_DB(mmsi)
    time.sleep(2)


