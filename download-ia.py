#!/usr/bin/python3
import requests
import json
import argparse
import os

platforms=[
        {"name":"saturn","collection":"redump.sega_saturn"},
        {"name":"dreamcast","collection":"redump.sega_dreamcast"},
        {"name":"wii","collection":["wiiusaredump","wiiusaredump2","wiiusaredump3"]}
    ]

def define_platform(platform):
    global collection
    for p in platforms:
        if platform.lower() in p["name"].lower():
            collection=p["collection"]
    response_API = requests.get('http://archive.org/metadata/' + collection + '/files/')
    return json.loads(response_API.text)['result']
        
def search(query):
    i=0
    print("ID\t Content\n====================")
    for f in files:
        if query.lower() in f["name"].lower():
            print(i,"\t",f["name"])
        i=i+1

def download(content_id):
    if content_id >= len(files):
        print("The requested content does not exist.")
        os._exit(1)
    content=files[content_id]
    #print(content["name"])
    response = requests.get('http://archive.org/download/'+collection+"/"+content["name"]+'/')
    if response.status_code > 400:
        print("The download request has exited with error",response.status_code,".")
        os._exit(1)
    content_files=json.loads(extract_content_files(response.text))

def extract_content_files(html):
    table_html=html.split("table")
    return (
        "["+table_html[1]
            .replace("class=\"archext\">","") #undesired content
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
            .replace("\n","")
            .replace("}{","},{")#comma separated  between objects
            +"]"
    )

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
