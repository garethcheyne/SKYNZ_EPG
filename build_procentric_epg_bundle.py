
import requests
import time
from datetime import datetime, timezone, timedelta, date
import pytz
import json
from zipfile import ZipFile
import pandas as pd
import yaml
from yaml.loader import SafeLoader
import ftplib
from anyascii import anyascii

## EPG URL 
## "https://web-epg.sky.co.nz/prod/epgs/v1?start=1656804027242&end=1656832827242&limit=20000"


URI_EPG = "https://web-epg.sky.co.nz/prod/epgs/v1?"
URI_CHANNELS = "https://skywebconfig.msl-prod.skycloud.co.nz/sky/json/channels.prod.json"

def push2FTP(file_name):

    with open("credentials.yaml") as f:
        config = yaml.load(f, Loader=SafeLoader)
        f.close()

    ftp = ftplib.FTP()
    ftp.connect(config["server"], config["port"])
    ftp.login(config["username"], config["password"])

    with open(f"./export/NZL/{file_name}", "rb") as file:
        ftp.storbinary(f'STOR .{config["dir"]}/{file_name}', file)

    print("Process Complete")
    exit()


def getRawEPG():
    now = datetime.now(pytz.timezone("Pacific/Auckland"))
    dateTimeStart = now + timedelta(hours=0)
    dateTimeEnd = now + timedelta(hours=72)

    timeStart = str(datetime.timestamp(dateTimeStart)*1000).replace(".","")[0:13]
    timeEnd = str(datetime.timestamp(dateTimeEnd)*1000).replace(".","")[0:13]
    uri = "%sstart=%s&end=%s&limit=20000" % (URI_EPG, timeStart, timeEnd)

    responce = requests.get(uri)

    if responce.status_code == 200:
        with open("./data/raw_epg.json", "w") as f:
            json.dump(responce.json(), f, indent=6)
            f.close()
        return responce.json()
    exit()


def getRawChannels():
    uri = URI_CHANNELS
    responce = requests.get(uri) 

    if responce.status_code == 200:
        data = responce.json()
        with open("./data/raw_channels.json", "w") as f:
            json.dump(data, f, indent=6)
            f.close()

        exportChannelMaping(data)

        return responce.json()

def exportChannelMaping(data):
    pop = {"genre", "sort", "synopsis", "promotions","logo","sku", "order","url","logoInverted","promotionIntro"}

    for c in data:
        c["EPG_Map_No"] = c.pop("number")
        c["Channel_Name"] = c.pop("name")
        c["Logo_Url"] = c.pop("logoThumbnail")
        c["HD"] = c.pop("hd")
        c["Genre"] = c["genre"][0]

        for p in pop:
            c.pop(p)

    df = pd.read_json(json.dumps(data), orient="records")
    df.to_csv("./data/raw_channels.csv", index=False)

def duration(start, end):
    millis = int(end) - int(start)
    secounds = (millis/1000)
    duration = str((secounds/60))[0:-2]     
    return duration

def date(start):
    unix_ts = int(start[0:10])
    utc_time = datetime.fromtimestamp(unix_ts)    
    return utc_time.strftime("%Y-%m-%d")

def time(start):
    unix_ts = int(start[0:10])
    utc_time = datetime.fromtimestamp(unix_ts)    
    return utc_time.strftime("%H%M")

def modelEPG(rawEPG):
    events = rawEPG["events"]

    channels = []
    this_events = []

    for event in events:
        this_event = {
            "eventID": f'{event["channelNumber"]}-{event["id"]}',
            "title": anyascii(event["title"]),
            "eventDescription": anyascii(event["synopsis"]) ,
            "rating": None, #event["rating"],
            "date": date(event["start"]),
            "startTime": time(event["start"]),
            "length": duration(event["start"], event["end"]),
            "genre" : event["genres"][0],
            "channelNumber": event["channelNumber"] # Removed Later
        }

        this_events.append(this_event)

    return this_events

def groupEPGChannels(events):
    rawChannels = getRawChannels()
    channels = []

    for c in rawChannels:
        epg = [x for x in events if (x['channelNumber'] == int(c["number"]))]
        #if(len(epg) != 0):
        channel ={}
        channel["channelID"] = "NZL_" + str(int(c["number"]))
        channel["name"] = c["name"]
        channel["resolution"] = "HD" if c["hd"] == "true" else "SD"
        channel["events"] = epg
        channels.append(channel)

    for channel in channels:
        for event in channel["events"]:
            if "channelNumber" in event.keys():
                del event["channelNumber"]

    return channels



def getMaxMinutes(epg):
    maxMin = 0
    for channel in epg:
        for event in channel['events']:
            maxMin = maxMin + int(event["length"])
    return maxMin



def buildPayLoad(epg):
    fetchTime =  datetime.now(pytz.timezone("Pacific/Auckland"))

    payload = {
        "filetype": "Pro:Centric JSON Program Guide Data NZL",
        "version": "0.1",
        "fetchTime": fetchTime.strftime('%Y-%m-%dT%H:%M:%S+0000'),
        "maxMinutes": getMaxMinutes(epg),
        "channels": epg
    }

    with open("./data/Procentric_EPG.json", "w") as f:
        json.dump(payload, f, indent=6, ensure_ascii=True)
        f.close()

    return payload


def saveToZip(payload):
    #Zip file name : Procentric_EPG_{country code}_{date}.zip (e.g. Procentric_EPG_GBR_20220609.zip)

    today = datetime.today().date().strftime("%Y%m%d")

    file_name = f"Procentric_EPG_NZL_{today}.zip"
    with ZipFile(f"/home/procentric/EPG/NZL/{file_name}", 'w') as zip:
        zip.write("./data/Procentric_EPG.json", "Procentric_EPG.json")
        zip.close()

    return file_name




def Main():
    ## Get EPG From SKY NZ API
    raw_epg = getRawEPG()

    ## Process Events
    events = modelEPG(raw_epg)

    ## Group Events per Channel
    epg = groupEPGChannels(events)

    ## Build ProCentric JSON PayLoad
    payload = buildPayLoad(epg)

    # Add ProCentric JSON to ZIP
    file_name = saveToZip(payload)

    ## Upload to FTP
    ##push2FTP(file_name)


Main()
