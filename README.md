# SKY New Zealand EPG Data Export.

ALPHA ONLY, NOT COMPLETE, NOT TESTED AND WORKING.

The following uses the Sky NZ EPG API to extract the current days channel information and prepaid that data for importation into LG ProCentric.

Feel free to use this as a base if you want needing NZ EPG data including all Sky NZ channels and model as you see fit.


## How to Use.
Clone this Repo.
Create the Python venv
Install Pip Requirements
Create a Credentials.yaml file in the root
TEST
Schedual Task, Daily


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




## LG ProCentric 
Preparing the data form importation is only the first step, you must host a Zip file on and accessable FTP server and have the files names correctly.

ZIP Naming Convention = Procentric_EPG_{ISO Country Code ie NZL}_{Date YYYYMMDD}.zip

JSON Naming Convention = Procentric_EPG.json

### Expected JSON Format
```
{
    "filetype": "Pro:Centric JSON Program Guide Data 98101",
    "version": "0.1",
    "fetchTime": "2022-06-24T13:22:44-0400",
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

### EPG ID Mapping.
[EPG ID Mapping](./data/raw_channels.csv)

