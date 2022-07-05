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
    dateTimeStart = now + timedelta(hours=12)
    dateTimeEnd = now + timedelta(hours=24)

    timeStart = str(datetime.timestamp(dateTimeStart)*1000).replace(".","")[0:13]
    timeEnd = str(datetime.timestamp(dateTimeEnd)*1000).replace(".","")[0:13] 
    uri = "%sstart=%s&end=%s&limit=2000" % (URI_EPG, timeStart, timeEnd)
   
    responce = requests.get(uri)     
    if responce.status_code == 200:
        with open("./data/raw_epg.json", "w") as f:
            json.dump(responce.json(), f, indent=6)
            f.close()
        return responce.json()

    return responce.json()


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

    for event in events:
        event["eventID"] = event.pop("id")
        event["title"] = event.pop("title")
        event["eventDescription"] = event.pop("synopsis")
        event["date"] =  date(event["start"])
        event["startTime"] = time(event["start"])
        event["length"] = duration(event["start"], event["end"])
        event["genres"] = event["genres"][0]
        event.pop("start")
        event.pop("end")

        if "seriesId" in event:
            event.pop("seriesId")

    return events

def groupEPGChannels(events):
    rawChannels = getRawChannels()
    channel = {}
    channels = []

    for c in rawChannels:
        epg = [x for x in events if (x['channelNumber'] == int(c["number"]))]

        channel["channelID"] = int(c["number"])
        channel["name"] = c["name"]
        channel["resolution"] = "HD" if c["hd"] == "true" else "SD"
        channel["events"] = epg
        channels.append(channel)

    for channel in channels:
        for event in channel["events"]:
            if "channelNumber" in event.keys():
                del event["channelNumber"]
                print("ok")

    return channels
    


def getMaxMinutes(epg):
    maxMin = 0
    for channel in epg:
        for event in channel['events']:
            maxMin = maxMin + int(event["length"])
    return maxMin



def buildPayLoad(epg):   

    payload = {
        "filetype": "Pro:Centric JSON Program Guide Data",
        "version": "0.1",
        "fetchTime": str(datetime.now(pytz.timezone("Pacific/Auckland"))),
        "maxMinutes": getMaxMinutes(epg),
        "channels": epg            
    }

    with open("./data/Procentric_EPG.json", "w") as f:
        json.dump(payload, f, indent=6)
        f.close()

    return payload


def saveToZip(payload):
    #Zip file name : Procentric_EPG_{country code}_{date}.zip (e.g. Procentric_EPG_GBR_20220609.zip)

    today = datetime.today().date().strftime("%Y%m%d")

    file_name = f"Procentric_EPG_NZL_{today}.zip"
    with ZipFile(f"./export/NZL/{file_name}", 'w') as zip:
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
    #push2FTP(file_name)


Main()