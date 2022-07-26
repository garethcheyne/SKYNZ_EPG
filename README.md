# SKY New Zealand EPG Data Export.

ALPHA ONLY, NOT COMPLETE, NOT TESTED OR CONFIRMED WORKING.

The following uses the Sky NZ EPG API to extract the current days channel information and prepairs that data for importation into a LG ProCentic Server, after it has been uploaded the an ftp server accessable to the PCS.

Feel free to use this as a base if you want an NZ EPG data including all Sky NZ channels and model as you see fit.


## How to Use.
1. Clone this Repo.
2. Create the Python venv
3. Install Pip Requirements
4. Create a "credentials.yaml" file in the root
5. !IMPORTANT -> TEST
6. Schedule Task, Daily


## SKY NZ API (No Channel Info)
URL https://web-epg.sky.co.nz/prod/epgs/v1?start={unix_timestamp}&end={unix_timestamp}&limit=20000

### PayLoad Responce
```
{
    "total": 947,
    "returned": 947,
    "events": [
        {
        "id": "047548170",
        "title": "The Great British Sewing Bee",
        "synopsis": "The fashion industry is the biggest polluter of our planet next to oil, so for the first time on The Great British Sewing Bee, it is Reduce, Reuse and Recycle Week.",
        "channelNumber": 1,
        "start": "1656802800000",
        "end": "1656806400000",

        "genres": [
        "General Entertainment"
        ],
        "rating": "G",
        "seriesId": "23551"
        }
    ]
}
```

### Error Responce, 
Useful if you want to add further queries in the url.
```
{
    "code" : "NO_RESULTS_FOUND",
    "description" : "No results found",
    "message" : "EpgSearchRequest{  
        id=\'null\'  
        title=\'null\', 
        alias=\'selepgsalias\', 
        genre=\'null\', 
        channelNumber=\'null\', 
        limit=\'2000\', 
        offset=\'null\', 
        synopsis=null, 
        seriesId=null, 
        start=16568056427465026, 
        end=1656832827242, 
        numberOfDays=null, 
        numberOfHours=null, 
        inflight=true, 
        includeAdultContent=false, 
        fields=null, 
        sortBy=null, 
        dateFormat=null, 
        timeZone=UTC, 
        dataformat=JSON
    }"
```


## SKY Channel Names and Info
URL https://skywebconfig.msl-prod.skycloud.co.nz/sky/json/channels.prod.json




## LG ProCentric Server
Preparing the data form importation is only the first step, you must host a Zip file on and accessable FTP server and has the file named correctly.

ZIP Naming Convention = Procentric_EPG_{ISO Country Code ie NZL}_{Date YYYYMMDD}.zip

JSON Naming Convention = Procentric_EPG.json

JSON payload needs to be enclosed into the the ZIP file and places in the approperate directory for collections over FTP.

### FTP Service
Your file needs to sit in a sub directory from a logged in FTP user.

Linux Users prospective
/home/procentric/EPG/NZL

FTP Users prospective
/EPG/NZL


### Expected JSON Format
```
{
    "filetype": "Pro:Centric JSON Program Guide Data NZL",
    "version": "0.1",
    "fetchTime": "2022-06-24T13:22:44+1200",
    "maxMinutes": 60,
    "channels": [
        {
            "channelID": "1",
            "name": "TVNZ One",
            "resolution": "HD",
            "events": [
                {
                    "eventID": "334242",
                    "title": "6 News",
                    "eventDescription": TVNZ New Zealand News",
                    "rating": "TV-MA",
                    "date": "2022-06-25",
                    "startTime": "1800",
                    "length": "60",
                    "genre": "News"
                }
            ]
        }
    ]
}
```


### EPG ID Mapping for PCD or Other.
[EPG ID Mapping](./data/raw_channels.csv)

## Channel Icon Bundle

Will build and bundle the NZ Channels icon bundle for importing into PCD.

