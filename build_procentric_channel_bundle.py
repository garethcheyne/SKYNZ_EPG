import requests
import os
import json
from zipfile import ZipFile
from datetime import datetime

URI_CHANNELS = "https://skywebconfig.msl-prod.skycloud.co.nz/sky/json/channels.prod.json"


def getRawChannels():
    response = requests.get(URI_CHANNELS)

    if response.status_code == 200:
        return response.json()

def makeZip():

    file_name = f"channelIconsBundle.zip"
    with ZipFile(f"./export/ProCentric/ChannelBundle/{file_name}", 'w') as zip:
        zip.write("./data/bundle.properties", "bundle.properties")
        zip.write("./data/iconMap.txt", "iconMap.txt")
        for file_name in os.listdir("./data/channelIcons"):
            zip.write(f"./data/channelIcons/{file_name}", f"channelIcons/{file_name}")
        zip.close()

def makePopsFile():

    today = f'date = {datetime.today().date().strftime("%d/%m/%y")}\n'
    version = f'version = {datetime.today().date().strftime("%Y.%m.%d")}\n'

    with open(f"./data/bundle.properties", "w") as f:

        f.writelines(["# Channel Icons Properties File\n"])
        f.writelines(["type = channelIcons\n"])
        f.writelines(["name = NZ Channel Icons\n"])
        f.writelines(["region = New Zealand\n"])
        f.writelines(["description = Channel Icons for NZ including SKYNZ\n"])
        f.writelines([version])
        f.writelines(["author = Gareth Cheyne\n"])
        f.writelines([today])
    f.close()


def getChannelThumbnails():

    channels = getRawChannels()

    with open(f"./data/iconMap.txt", "w") as f_map:

        f_map.writelines(["## iconsMap.txt\n"])
        f_map.writelines(["# ID | filename | name | alias (optional)\n"])

        for channel in channels:
            response = requests.get(channel["logoThumbnail"])
            if response.status_code == 200:

                file_name = channel["logoThumbnail"].split("/")[-1].replace("-","_").lower()

                f_map.writelines([f"{channel['number']} | {file_name} | {channel['name']}\n"])
            
                with open(f"./data/channelIcons/{file_name}", "wb") as f_icon:
                    f_icon.write(response.content)
                    f_icon.close()
        f_map.close()
    
    makePopsFile()
    makeZip()


getChannelThumbnails()