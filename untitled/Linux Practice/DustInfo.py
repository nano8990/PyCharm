import urllib.request
import pandas as pd
from bs4 import BeautifulSoup
import requests

import xml.etree.ElementTree as ET
from xml.etree.ElementTree import parse, Element

baseUrl = "http://openapi.airkorea.or.kr/openapi/services/rest/ArpltnInforInqireSvc/getCtprvnMesureLIst"
itemCode = ['SO2', 'CO', 'O3', 'NO2', 'PM10', 'PM25']
dataGubun = 'HOUR'
pageNo = '1'
numOfRows = '25'
serviceKey = 'aDTqxJKNQ6XA6akRhrCF1ZSGXu8uk6HwyjXEWNetiKZEo%2FAD1M38g97KxPIXwL5k4RBnx%2BJwa6DzpTgn0G6AEg%3D%3D'
regionNames = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주', '세종']

xmlUrlList = []
for itemCodeValue in itemCode:
    xmlUrl = baseUrl + '?'
    xmlUrl += 'itemCode' + '=' + itemCodeValue + '&'
    xmlUrl += 'dataGubun' + '=' + dataGubun + '&'
    xmlUrl += 'pageNo' + '=' + pageNo + '&'
    xmlUrl += 'numOfRows' + '=' + numOfRows + '&'
    xmlUrl += 'ServiceKey' + '=' + serviceKey
    xmlUrlList.append(xmlUrl)
for eachXmlUrl in xmlUrlList:
    request = urllib.request.Request(eachXmlUrl)
    request.get_method = lambda: 'GET'
    response_body = urllib.request.urlopen(request).read()
    fullXmlString = str(response_body, "utf-8")

    result = []
    root = ET.fromstring(fullXmlString)
    elements = root.findall('body/items/item')
    for item in elements:
        try:
            item_list = []
            item_list.append(item.find('dataTime').text)
            item_list.append(item.find('itemCode').text)
            item_list.append(item.find('dataGubun').text)
            item_list.append(item.find('seoul').text)
            item_list.append(item.find('busan').text)
            item_list.append(item.find('daegu').text)
            item_list.append(item.find('incheon').text)
            item_list.append(item.find('gwangju').text)
            item_list.append(item.find('daejeon').text)
            item_list.append(item.find('ulsan').text)
            item_list.append(item.find('gyeonggi').text)
            item_list.append(item.find('gangwon').text)
            item_list.append(item.find('chungbuk').text)
            item_list.append(item.find('chungnam').text)
            item_list.append(item.find('jeonbuk').text)
            item_list.append(item.find('jeonnam').text)
            item_list.append(item.find('gyeongbuk').text)
            item_list.append(item.find('gyeongnam').text)
            item_list.append(item.find('jeju').text)
            item_list.append(item.find('sejong').text)
            result.append(item_list)
        except Exception as e:
            print('This  row will be ignored', item_list)

    for i in range(0, len(regionNames)):
        tempCount = True
        for eachList in result:
            if tempCount == True:
                print(regionNames[i] + '의 ' + eachList[1] + ' ' + eachList[2])
                tempCount = False
            print(eachList[0] + ' : ' + eachList[i + 3])
        print()