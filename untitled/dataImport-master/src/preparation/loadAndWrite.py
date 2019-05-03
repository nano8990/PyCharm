import requests #Used to service API connection
from lxml import html #Used to parse XML
from bs4 import BeautifulSoup #Used to read XML table on webpage
import pandas as pd
from common import cFunction as cf
import numpy as np
import wget

# get dataList from filesystem to load and write
#dataList = pd.read_excel("../../data/inbound/dataList.xlsx")

# get dataList from spreadsheet to load and write
dataList = pd.read_csv("https://docs.google.com/spreadsheets/d/1VngqG-m7G8k1587c21MZoheR1Fz3amp1mJtiBvA1Jb0/export?format=csv&gid=0")
print("### The total number of target data is " + str(len(dataList)))

# Filtering -> get dataList only defined url
dataList = dataList[   dataList['사이트'].notnull() ]
print(dataList[["사이트"]])
print("### The total number of filtered data is " + str(len(dataList)))

###################################################
# Filtering -> for your own object
#dataList = dataList[   dataList['번호'] == "352" ]
###################################################

# create folder to save result
outPath = "../../data/outbound/"
folderList = dataList["폴더명"].tolist()
for i in folderList:
    cf.createFolder(outPath+i)

dataList = dataList.fillna("")
dataList = dataList.reset_index(drop=True)

# get dataList to load and write
for dataCount in range(0,len(dataList)):

    inputUrl = dataList.loc[dataCount, "사이트"]
    inputKey = dataList.loc[dataCount, "서비스키"]
    inputParameter = dataList.loc[dataCount, "파라미터"]
    inputFolder = dataList.loc[dataCount, "폴더명"]
    inputFile = dataList.loc[dataCount, "서비스명"]
    inputDataType = dataList.loc[dataCount, "데이터타입"]
    inputRefUrl = dataList.loc[dataCount, "참고문서"]
    inputRefType = dataList.loc[dataCount, "참고문서타입"]
    print(inputUrl)

    url = cf.makeURL(inputUrl,inputKey,inputParameter)
    print("fullUrl is " + url)

    newDF = pd.DataFrame()
    if (inputDataType == "xml"):
        newDF = cf.xmlProcess(url)
    elif(inputDataType == "json"):
        newDF = cf.jsonProcess(url)
    elif(inputDataType == "csv"):
        newDF = cf.csvProcess(url)

    fullOutPath = outPath+inputFolder+"/"+inputFolder+inputFile+".csv"
    print(fullOutPath)

    try:
        newDF.to_csv(fullOutPath, index=False, encoding="ms949")
    except Exception as x:
        print(x)

    fullOutRefPath = outPath + inputFolder + "/" + inputFolder + inputFile + "."+inputRefType
    try:
        wget.download(inputRefUrl, fullOutRefPath)
    except Exception as e:
        print(inputFolder+"참고문서 Error")
        print(e)
        pass