import os
import requests #Used to service API connection
from lxml import html #Used to parse XML
from bs4 import BeautifulSoup #Used to read XML table on webpage
import pandas as pd
from pandas.io.json import json_normalize

def makeURL(myUrl, myKey, myParameter):
    # myUrl = "http://192.168.1.120/index.php?"
    url = myUrl + myKey + "&" + myParameter

    url = url.rstrip('&')
    return url

def xmlProcess(url):
    response = requests.get(url)
    # Check if page is up
    if response.status_code == 200:
        # Convert webpage to %Data
        Data = BeautifulSoup(response.text, 'lxml-xml')
        result = []
        rows = 0
        columnName = []
        # search Item all item tag
        iterData = Data.find_all('item')
        for item in iterData:
            item_list = []
            # Fill the value in one row
            for tag in item.find_all():
                try:
                    tagname = tag.name
                    if rows == 0:
                        columnName.append(tagname)
                    item_list.append(item.find(tagname).text)
                except Exception as e:
                    print("This row will be ignored. ", item_list)
            rows = rows + 1
            result.append(item_list)
    finalResult = pd.DataFrame(result)
    finalResult.columns = columnName
    print(finalResult)
    return finalResult


def jsonProcess(url):

    # 정상 여부 확인 (200 정상)
    response = requests.get(url)
    # JSON 데이터 획득
    json = response.json()
    # PandasDataframe변환
    df = json_normalize(json)
    return df

def csvProcess(url):

    # 정상 여부 확인 (200 정상)
    response = requests.get(url)

    df = pd.read_csv(url, encoding="ms949")
    return df

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)
