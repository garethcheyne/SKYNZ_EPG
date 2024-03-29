
import requests
import time
from datetime import datetime, timezone, timedelta, date
import pytz
import json
from zipfile import ZipFile
import pandas as pd
import yaml
from yaml.loader import SafeLoader
from pathlib import Path
from anyascii import anyascii

## EPG URL 
## "https://web-epg.sky.co.nz/prod/epgs/v1?start=1656804027242&end=1656832827242&limit=20000"


# FIXED SKY URI's
URI_EPG = "https://web-epg.sky.co.nz/prod/epgs/v1?"
URI_CHANNELS = "https://skywebconfig.msl-prod.skycloud.co.nz/sky/json/channels.prod.json"

def get_config():
    with open("credentials.yaml") as f:
        global CONFIG 
        CONFIG = yaml.load(f, Loader=SafeLoader)
        f.close()


def get_raw_epg():
    now = datetime.now(pytz.timezone("Pacific/Auckland"))
    #start_of_day = now.strftime('%Y-%m-%d 00:00:00:00 %Z%z')

    # datetime_start = start_of_day + timedelta(hours=24)
    # datetime_end = start_of_day + timedelta(hours=48)

    datetime_start = now + timedelta(hours=0)
    datetime_end = now + timedelta(hours=48)

    #print(start_of_day)

    print(f"Start time: {datetime_start}, End Time: {datetime_end}")

    time_start = str(datetime.timestamp(datetime_start)*1000).replace(".","")[0:13]
    time_end = str(datetime.timestamp(datetime_end)*1000).replace(".","")[0:13]
    uri = "%sstart=%s&end=%s&limit=20000" % (URI_EPG, time_start, time_end)

    responce = requests.get(uri)

    if responce.status_code == 200:
        with open("./data/raw_epg.json", "w") as f:
            json.dump(responce.json(), f, indent=6)
            f.close()
        return responce.json()
    exit()


def get_raw_channels():
    uri = URI_CHANNELS
    responce = requests.get(uri) 

    if responce.status_code == 200:
        data = responce.json()
        with open("./data/raw_channels.json", "w") as f:
            json.dump(data, f, indent=6)
            f.close()

        export_channel_mapping(data)

        return responce.json()

def export_channel_mapping(data):
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

def shift_time(unix_timestamp):
    unix_timestamp = int(int(unix_timestamp) - 43200000) # 43200000 = 12hours
    shifted_time = int(str(unix_timestamp)[0:10])
    return shifted_time
   
def date(unix_ts):
    utc_time = datetime.fromtimestamp(shift_time(unix_ts))  
    return utc_time.strftime("%Y-%m-%d")

def time(unix_ts): 
    utc_time = datetime.fromtimestamp(shift_time(unix_ts))  
    return utc_time.strftime("%H%M")

def rating(event):
    if "rating" in event.keys():
        return event['rating']
    else:
        return None

def model_epg(raw_epg):

    events = raw_epg["events"]
    this_events = []

    for event in events:
        this_event = {
            "eventID": f'{event["channelNumber"]}-{event["id"]}',
            "title": anyascii(event["title"]),
            "eventDescription": anyascii(event["synopsis"]) ,
            "rating": None, #rating(event),
            "date": date(event["start"]),
            "startTime": time(event["start"]),
            "length": duration(event["start"], event["end"]),
            "genre" : event["genres"][0],
            "channelNumber": event["channelNumber"] 
        }

        this_events.append(this_event)

    return this_events

def group_epg_channels(events):
    raw_channels = get_raw_channels()
    channels = []

    for c in raw_channels:
        epg = [x for x in events if (x['channelNumber'] == int(c["number"]))]
        channel = {}
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



def get_max_minutes(epg):
    maxMin = 0
    for channel in epg:
        for event in channel['events']:
            maxMin = maxMin + int(event["length"])
    return maxMin



def build_payload(epg):
    fetchTime =  datetime.now(pytz.timezone("Pacific/Auckland"))

    payload = {
        "filetype": "Pro:Centric JSON Program Guide Data NZL",
        "version": "0.1",
        "fetchTime": fetchTime.strftime('%Y-%m-%dT%H:%M:%S%z'),
        "maxMinutes": get_max_minutes(epg),
        "channels": epg
    }

    with open("./data/Procentric_EPG.json", "w") as f:
        json.dump(payload, f, indent=6, ensure_ascii=True)
        f.close()

    return payload


def save_to_zip(payload):
    #Zip file name : Procentric_EPG_{country code}_{date}.zip (e.g. Procentric_EPG_GBR_20220609.zip)

    today = datetime.today().date().strftime("%Y%m%d")   

    file_name = f"Procentric_EPG_NZL_{today}.zip"

    with ZipFile(f"{CONFIG['local_dir']}{file_name}", 'w') as zip:
        zip.write("./data/Procentric_EPG.json", "Procentric_EPG.json")
        zip.close()

    print(f"Process Complete, File Saved {CONFIG['local_dir']}{file_name}")

    return file_name

def prune_old_epgs():
    [f.unlink() for f in Path(CONFIG['local_dir']).glob("*") if f.is_file()] 


def Director():
    ## Get Config 
    get_config()

    ## Prune old  EPG files.
    prune_old_epgs()

    ## Get EPG From SKY NZ API
    raw_epg = get_raw_epg()

    ## Process Events
    events = model_epg(raw_epg)

    ## Group Events per Channel
    epg = group_epg_channels(events)

    ## Build ProCentric JSON PayLoad
    payload = build_payload(epg)

    # Add ProCentric JSON to ZIP
    save_to_zip(payload)

Director()
