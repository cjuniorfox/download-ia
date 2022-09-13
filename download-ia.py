#!/usr/bin/python3
import requests
import json
import argparse
import os
from pathlib import Path
import html
import math
import time

platforms=[
        {"name":"saturn","collection":"redump.sega_saturn"},
        {"name":"dreamcast","collection":"redump.sega_dreamcast"},
        {"name":"wii","multi":[{"collection":"wiiusaredump"},{"collection":"wiiusaredump2"},{"collection":"wiiusaredump3"}]}
    ]

def define_platform(platform):
    global collection
    for p in platforms:
        if platform.lower() in p["name"].lower():
            if "collection" in p.keys():
                collection = p["collection"]
            if "multi" in p.keys() and isinstance(p["multi"], list):
                collection = p["multi"]
                start=0
                i=0
                files=[]
                for c in collection:
                    response_API = requests.get('http://archive.org/metadata/' + c["collection"] + '/files/')
                    files = files + json.loads(response_API.text)['result']
                    collection[i]["size"]=len(files)
                    i=i+1
                return files
    response_API = requests.get('http://archive.org/metadata/' + collection + '/files/')
    return json.loads(response_API.text)['result']
        
def search(query):
    i=0
    print("ID\t Content\n====================")
    for f in files:
        if query.lower() in f["name"].lower():
            print(i,"\t",Path(f["name"]).stem)
        i=i+1
def acquire_collection(content_id):
    for c in collection:
        if content_id < c["size"]:
            return c["collection"]

def get_download_col(content_id):
    if content_id >= len(files):
        print("The requested content does not exist.")
        os._exit(1)
    if isinstance(collection,str):
        return collection
    elif isinstance(collection,list):
        return acquire_collection(content_id)

def prepare_download(col,content):
    response = requests.get('http://archive.org/download/'+col+"/"+content["name"]+'/')
    if response.status_code > 400:
        print("The download request has exited with error",response.status_code,".")
        os._exit(1)
    return json.loads(extract_content_files(response.text))

def download_files(col,content_files,name):
    for f in content_files:
        if "url" in f.keys():
            file_name = f["name"]
            with requests.get("http:"+f["url"], stream=True) as r:
                r.raise_for_status()
                with open(os.path.join(name,os.path.basename(file_name)), 'wb') as f:
                    dot = ""
                    chunk_size=8192
                    size=0
                    print("Downloading \""+file_name+"\"")
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        size=chunk_size+size
                        print(" Fetched:",size_pretty(size),"          \r",end="")
                        f.write(chunk)
                    print("")

def download(content_id):
    start_time = time.time()
    col=get_download_col(content_id)
    content=files[content_id]
    name=Path(content["name"]).stem
    print("Preparing to download \""+name+"\".")
    content_files=prepare_download(col,content)
    print("Content list fetched. Downloading the content")
    if not os.path.exists(name):
        os.mkdir(name)
    download_files(col,content_files,name)
    print("All files downloaded. Time elapsed:", math.trunc(time.time() - start_time),"seconds.")

def size_pretty(size):
    if (size < 1024):
        return format(math.trunc(size))+" B"
    elif (size > 1024 and size < (1024 * 1024)):
        return format(math.trunc(size/1024))+" KB"
    elif (size > (1024 * 1024) and size < (1024 * 1024 * 1024)):
        return format(math.trunc(size/1024/1024))+" MB"
    elif (size > (1024 * 1024 * 1024)):
        return format(math.trunc(size/1024/1024/1024/1024))+" GB"

def validate_json(json_data):
    try:
        json.loads(json_data)
    except ValueError as err:
        return False
    return True

def extract_content_files(payload):
    table_html=payload.split("table")
    challenge_json=html.unescape(
        table_html[1]
            .replace("\n","")
            .replace(" class=\"archext\">","") #undesired content
            .replace("<caption>","{\"caption\":\"") #first value is caption
            .replace("</caption>","\"},")
            .replace("<tr><th>file<th>as jpg<th>timestamp<th>size</tr>","") #removing table header
            .replace("<tr>","{\"")#table line to json object
            .replace("</tr>","\"}")
            .replace("<td><a href=","url\":")#link field
            .replace("</a><td><td>","\",\"date_time\":\"") #date_time field
            .replace("<td id=\"size\">","\",\"size\":\"") #size field
            .replace("</","") #remove last undesired character
            .replace(">",",\"name\":\"") #name for the link extracted before
            .replace("}{","},{")#comma separated  between objects
    )
    #split resultant json and challenge against validation
    json_resultant_list = []
    for d in challenge_json.split("},{"):
        if validate_json("{"+d+"}"):
            json_resultant_list.append("{"+d+"}")
        elif validate_json("{"+d):
            json_resultant_list.append("{"+d)
        elif validate_json(d+"}"):
            json_resultant_list.append(d+"}")
    return "["+(",".join(json_resultant_list))+"]"
    return result

parser = argparse.ArgumentParser(description="Internet Archive video game console contents downloader")
parser.add_argument("--platform", "-p", metavar="saturn", type=str , help="Video game platform console wanted")
parser.add_argument("--search", "-s", metavar="sonic", type=str, help="Content wanted")
parser.add_argument("--download", "-d", metavar="1730", type=int, help="Game ID obained from search result")
args = parser.parse_args()

if args.platform :
    files = define_platform(args.platform)
else :
    print("Platform it's required. Call it again with -p or --platform parameter")
    os._exit(1)

if args.search :
    search(args.search)
if args.download:
    download(args.download)
