import hashlib
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
import json
import re
from urllib.parse import parse_qs
import threading
import cgi
import uuid

import pandas as pd
from sqlalchemy import create_engine, types
import cx_Oracle as oci # for connect Oracle Database

import codecs
from random import *


PORT_NUMBER = 8099
db_ip = '192.168.110.3'
db_port = '1522'
db_serviceName = 'xe'
db_id = 'DJ2019'
db_pw = 'DJ2019'

db_userTableName = 'BPS_USERS'
db_userTableColumns = ('USERID', 'USERKEY', 'BALANCE', 'USABLE_AMOUNT')
db_blockTableName = 'BPS_BLOCK'
db_blockTableColumns = ('BLOCKINDEX', 'PREVIOUSHASH', 'TIMESTAMP', 'DATA', 'CURRENTHASH', 'PROOF')
db_txTableName = 'BPS_TXDATA'
db_txTableColumns = ('COMMIT_YN', 'SENDER', 'AMOUNT', 'RECEIVER', 'UUID')
# db_nodeListTableName = 'BPS_NODELIST'
# db_nodeListTableColumns = ('IP', 'PORT', 'CONNECTION_FAIL')

# g_receiveNewBlock = "/node/receiveNewBlock"
g_difficulty = 1
g_maximumTry = 100
# g_nodeList = {'192.168.110.28':'8099'}

count = 0
count2 = 0

class Block:

    def __init__(self, index, previousHash, timestamp, data, currentHash, proof):
        self.index = index
        self.previousHash = previousHash
        self.timestamp = timestamp
        self.data = data
        self.currentHash = currentHash
        self.proof = proof

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class txData:

    def __init__(self, commitYN, sender, amount, receiver, uuid):
        self.commitYN = commitYN
        self.sender = sender
        self.amount = amount
        self.receiver = receiver
        self.uuid = uuid


def makeCreateTableQuery(tableName, columns):
    print('\tFunction "makeCreateTableQuery" executed')

    if (tableName == 'BPS_BLOCK'):
        createTableQuery = "CREATE TABLE BPS_BLOCK(\
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (64) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (500) NOT NULL, \
        %s VARCHAR2 (64) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        CONSTRAINTS PK_BPS_BLOCK PRIMARY KEY(BLOCKINDEX) \
        )" % columns

    if (tableName == 'BPS_TXDATA'):
        createTableQuery = "CREATE TABLE BPS_TXDATA(\
        %s VARCHAR2 (1) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        CONSTRAINTS PK_BPS_TXDATA PRIMARY KEY(UUID) \
        )" % columns

    if (tableName == 'BPS_NODELIST'):
        createTableQuery = "CREATE TABLE BPS_NODELIST(\
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL \
        )" % columns

    if (tableName == 'BPS_USERS'):
        createTableQuery = "CREATE TABLE BPS_USERS(\
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        %s VARCHAR2 (100) NOT NULL, \
        CONSTRAINTS PK_BPS_USERS PRIMARY KEY(USERKEY) \
        )" % columns

    return createTableQuery

def makeDropTableQuery(tableName):
    print('\tFunction "makeDropTableQuery" executed')

    dropTableQuery = 'DROP TABLE %s' % tableName

    return dropTableQuery

def makeUpdateQuery(tableName, setValue, whereCondition):
    print('\tFunction "makeUpdateQuery" executed')
    setValueInput = ''
    for key, value in setValue.items():
        setValueInput += str(key)
        setValueInput += ' = '
        if (isNumber(value)):
            setValueInput += "%s" % str(value)
        else:
            setValueInput += "'%s'" % str(value)
        setValueInput += ', '
    setValueInput = setValueInput.rstrip(', ')

    whereConditionInput = ''
    for key, value in whereCondition.items():
        if (type(value) == list):
            whereConditionInput += '('
            for eachValue in value:
                whereConditionInput += str(key)
                whereConditionInput += ' = '
                if (isNumber(eachValue)):
                    whereConditionInput += str(eachValue)
                else:
                    whereConditionInput += "'%s'" % str(eachValue)
                whereConditionInput += ' OR '
            whereConditionInput = whereConditionInput.rstrip(' OR ')
            whereConditionInput += ')'
        else:
            whereConditionInput += str(key)
            whereConditionInput += ' = '
            if (isNumber(value)):
                whereConditionInput += str(value)
            else:
                whereConditionInput += "'%s'" % str(value)
        whereConditionInput += ' AND '
    whereConditionInput = whereConditionInput.rstrip(' AND ')
    updateQuery = 'UPDATE %s SET %s WHERE %s' % (tableName, setValueInput, whereConditionInput)
    return updateQuery

def insertData(tableName, **kwargs):
    print('\tFunction "insertData" executed')
    connectComplete = False
    cursorComplete = False

    try:
        connectInfo = db_id + '/' + db_pw + '@' + db_ip + ':' + db_port + '/' + db_serviceName
        oracleConnection = oci.connect(connectInfo)
        connectComplete = True
        oracleCursor = oracleConnection.cursor()
        cursorComplete = True

        detailInsert = ''
        for (key, value) in kwargs.items():
            detailInsert += ':%s, ' % str(key)
        detailInsert = detailInsert.rstrip(', ')
        insertQuery = 'INSERT INTO %s VALUES(%s)' % (tableName, detailInsert)
        oracleCursor.execute(insertQuery, kwargs)
        oracleConnection.commit()

        oracleCursor.close()
        oracleConnection.close
        return True
    except:
        if (cursorComplete == False):
            oracleCursor.close()
        if (connectComplete == False):
            oracleConnection.close
        return False

def selectTable(tableName, columns, whereCondition=None):
    print('\tFunction "selectTable" executed')
    connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
    engine = create_engine(connectInfo)

    if (whereCondition != None):
        whereConditionInput = ''
        for key, value in whereCondition.items():
            if (type(value) == list):
                whereConditionInput += '('
                for eachValue in value:
                    whereConditionInput += str(key)
                    whereConditionInput += ' = '
                    if (isNumber(eachValue)):
                        whereConditionInput += str(eachValue)
                    else:
                        whereConditionInput += "'%s'" % str(eachValue)
                    whereConditionInput += ' OR '
                whereConditionInput = whereConditionInput.rstrip(' OR ')
                whereConditionInput += ')'
            else:
                whereConditionInput += str(key)
                whereConditionInput += ' = '
                if (isNumber(value)):
                    whereConditionInput += str(value)
                else:
                    whereConditionInput += "'%s'" % str(value)
            whereConditionInput += ' AND '
        whereConditionInput = whereConditionInput.rstrip(' AND ')
        selectQuery = 'SELECT * FROM %s WHERE %s' % (tableName, whereConditionInput)
    else:
        selectQuery = 'SELECT * FROM %s' % tableName

    try:
        resultData = pd.read_sql_query(selectQuery, engine)
    except:
        print('Table select error, There are no table named "%s" in db. \n It will be created' % tableName)
        createTable(tableName, columns)
        resultData = pd.read_sql_query(selectQuery, engine)
    resultData.rename(columns=lambda x: x.strip().upper(), inplace=True)
    return resultData


def createTable(tableName, columns):
    print('\tFunction "createTable" executed')

    connectComplete = False
    cursorComplete = False

    try:
        connectInfo = db_id + '/' + db_pw + '@' + db_ip + ':' + db_port + '/' + db_serviceName
        oracleConnect = oci.connect(connectInfo)
        connectComplete = True
        oracleCursor = oracleConnect.cursor()
        cursorComplete = True

        createTableQuery = makeCreateTableQuery(tableName, columns)
        oracleCursor.execute(createTableQuery)
        oracleConnect.commit()
        oracleCursor.close()
        oracleConnect.close
        return True

    except:
        if (cursorComplete == True):
            oracleCursor.close()
        if (connectComplete == True):
            oracleConnect.close
        return False

def replaceTable(tableName, columns):
    print('\tFunction "replaceTable" executed')
    connectComplete = False
    cursorComplete = False

    try:
        connectInfo = db_id + '/' + db_pw + '@' + db_ip + ':' + db_port + '/' + db_serviceName
        oracleConnect = oci.connect(connectInfo)
        connectComplete = True
        oracleCursor = oracleConnect.cursor()
        cursorComplete = True

        dropTableQuery = makeDropTableQuery(tableName)
        try:
            oracleCursor.execute(dropTableQuery)
        except:
            pass
        createTableQuery = makeCreateTableQuery(tableName, columns)
        oracleCursor.execute(createTableQuery)
        oracleConnect.commit()
        oracleCursor.close()
        oracleConnect.close

    except:
        if (cursorComplete == True):
            oracleCursor.close()
        if (connectComplete == True):
            oracleConnect.close


def updateTable(tableName, setValue, whereCondition):
    print('\tFunction "updateTable" executed')

    connectComplete = False
    cursorComplete = False

    try:
        connectInfo = db_id + '/' + db_pw + '@' + db_ip + ':' + db_port + '/' + db_serviceName
        oracleConnect = oci.connect(connectInfo)
        connectComplete = True
        oracleCursor = oracleConnect.cursor()
        cursorComplete = True

        updateQuery = makeUpdateQuery(tableName, setValue, whereCondition)
        oracleCursor.execute(updateQuery)
        oracleConnect.commit()
        oracleCursor.close()
        oracleConnect.close

    except:
        if (cursorComplete == True):
            oracleCursor.close()
        if (connectComplete == True):
            oracleConnect.close

def isNumber(s):
    if (type(s) == int or type(s) == float):
        return True
    else:
        return False

def transferInfoCheck(senderUserkey, receiverUserkey, amount, uuid):
    print('Function "transferInfoCheck" executed')

    whereCondition = {}
    whereCondition['UUID'] = uuid
    txData = selectTable(db_txTableName, db_txTableColumns, whereCondition)
    if txData['COMMIT_YN'][0] != '0':
        return "ALREADY_MINED"

    whereCondition = {}
    whereCondition['USERKEY'] = senderUserkey
    senderData = selectTable(db_userTableName, db_userTableColumns, whereCondition)
    if (len(senderData) == 0):
        print("No sender matched")
        return "USER_INFO_NOT_MATCH"

    whereCondition = {}
    whereCondition['USERKEY'] = receiverUserkey
    receiverData = selectTable(db_userTableName, db_userTableColumns, whereCondition)
    if (len(receiverData) == 0):
        print("No receiver matched")
        return "USER_INFO_NOT_MATCH"

    resultMessage = moneyTransferCommit(senderData, receiverData, amount, uuid)

    return resultMessage

def moneyTransferCommit(senderData, receiverData, amount, uuid):

    if (float(senderData['BALANCE'][0]) >= amount):
        setValue = {}
        setValue['BALANCE'] = float(senderData['BALANCE'][0]) - float(amount)
        whereCondition = {}
        whereCondition['USERID'] = senderData['USERID'][0]
        whereCondition['USERKEY'] = senderData['USERKEY'][0]
        updateTable(db_userTableName, setValue, whereCondition)

        setValue = {}
        setValue['BALANCE'] = float(receiverData['BALANCE'][0]) + float(amount)
        setValue['USABLE_AMOUNT'] = float(receiverData['USABLE_AMOUNT'][0]) + float(amount)
        whereCondition = {}
        whereCondition['USERID'] = receiverData['USERID'][0]
        whereCondition['USERKEY'] = receiverData['USERKEY'][0]
        updateTable(db_userTableName, setValue, whereCondition)

        return "SUCCESS"

    else:
        return "LACK_OF_BALANCE"

def generateGenesisBlock():
    print('\tFunction "generateGenesisBlock" executed')
    timestamp = time.time()
    print("time.time() => %f \n" % timestamp)
    tempHash = calculateHash(0, '0', timestamp, "Genesis Block", 0)
    print(tempHash)
    return Block(0, '0', timestamp, "Genesis Block",  tempHash, 0)

def calculateHash(index, previousHash, timestamp, data, proof): #해쉬계산 블록번호, 이전블록 해쉬, 거래시간, 데이터, 작업증명을 넣어서 하고 16진수로 바꿈
    print('\tFunction "calculateHash" executed')
    value = str(index) + str(previousHash) + str(timestamp) + str(data) + str(proof)
    sha = hashlib.sha256(value.encode('utf-8'))
    return str(sha.hexdigest())

def calculateHashForBlock(block): #위에 있는 해쉬를 call
    print('\tFunction "calculateHashForBlock" executed')
    return calculateHash(block.index, block.previousHash, block.timestamp, block.data, block.proof)

def getLatestBlock(blockchain): #가장 최근의 블록
    print('\tFunction "getLatestBlock" executed')
    return blockchain[len(blockchain) - 1]

def generateNextBlock(blockchain, blockData, timestamp, proof): #다음블록생성
    print('\tFunction "generateNextBlock" executed')
    previousBlock = getLatestBlock(blockchain)
    nextIndex = int(previousBlock.index) + 1
    nextTimestamp = timestamp
    nextHash = calculateHash(nextIndex, previousBlock.currentHash, nextTimestamp, blockData, proof)
    # index, previousHash, timestamp, data, currentHash, proof
    return Block(nextIndex, previousBlock.currentHash, nextTimestamp, blockData, nextHash, proof)

def writeBlockchain(blockchain, id=None, key=None, mining=False):
    print('\tFunction "writeBlockchain" executed')
    blockchainList = []
    for block in blockchain:
        blockList = [str(block.index), str(block.previousHash), str(block.timestamp), str(block.data),
                     str(block.currentHash), str(block.proof)]
        blockchainList.append(blockList)

    connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
    engine = create_engine(connectInfo)

    blockReader = selectTable(db_blockTableName, db_blockTableColumns)

    lastLineNumber = len(blockReader)
    for i in range(lastLineNumber):
        lineNumber = i + 1
        if (lineNumber == lastLineNumber):
            line = blockReader.loc[i]
            lastBlock = Block(line[0], line[1], line[2], line[3], line[4], line[5])
    try:
        if (int(lastBlock.index) + 1 != int(blockchainList[-1][0]) or lastLineNumber + 1 != len(blockchainList)):
            print("Index sequence mismatch")
            if (lastBlock.index == str(blockchainList[-1][0])):
                print("DB has already been updated")
            return

    except:
        print(
            'Index search error, There are no data or Existing table have problems. \n It will be replaced by full data.')
        pass

    blockWriter = pd.DataFrame(blockchainList, columns=db_blockTableColumns)
    # convert type to varchar if the types of the columns of a dataframe is object
    replaceTable(db_blockTableName, db_blockTableColumns)
    try:
        to_varchar = {c: types.VARCHAR(blockWriter[c].str.len().max()) for c in
                      blockWriter.columns[blockWriter.dtypes == 'object'].tolist()}
        print(to_varchar)
        blockWriter.to_sql(db_blockTableName, engine, if_exists='append', index=False, dtype=to_varchar)
        print('Blockchain written to db')
        success = True

    except Exception as e:
        print(e)
        print(blockWriter)
        print(blockReader)
        print('Data save error, It seems to have an integrity or type problem.')
        to_varchar = {c: types.VARCHAR(blockReader[c].str.len().max()) for c in
                      blockReader.columns[blockReader.dtypes == 'object'].tolist()}
        blockReader.to_sql(db_blockTableName, engine, if_exists='append', index=False, dtype=to_varchar)
        success = False

    # update txData cause it has been mined.
    for block in blockchain:
        updateTx(block, id, key)

    if (mining == True):
        whereCondition = {}
        whereCondition["USERID"] = id
        whereCondition["USERKEY"] = key
        matchedUser = selectTable(db_userTableName, db_userTableColumns, whereCondition)
        if len(matchedUser) == 0:
            return

        userBalance = float(matchedUser["BALANCE"])
        userUsableAmount = float(matchedUser["USABLE_AMOUNT"])

        setValue = {}
        setValue["BALANCE"] = userBalance + 1000
        setValue["USABLE_AMOUNT"] = userUsableAmount + 1000
        updateTable(db_userTableName, setValue, whereCondition)

    return success
    # print('Broadcasting new block to other nodes')
    # broadcastNewBlock(blockchain)


def readBlockchain(tableName=db_blockTableName, columns=db_blockTableColumns, id=None, key=None,  mode='internal'):
    print('\tFunction "readBlockchain" executed')

    importedBlockchain = []

    blockReader = selectTable(tableName, columns)
    try:
        if len(blockReader) == 0:
            raise Exception
        for i in range(len(blockReader)):
            line = blockReader.loc[i]
            block = Block(line[0], line[1], line[2], line[3], str(line[4]), str(line[5]))
            importedBlockchain.append(block)
        print("success pulling blockchain from DB")
        return importedBlockchain
    except:
        if mode == 'internal':
            blockchain = generateGenesisBlock()
            importedBlockchain.append(blockchain)
            if (writeBlockchain(importedBlockchain, id, key)):
                whereCondition = {}
                whereCondition["USERID"] = id
                whereCondition["USERKEY"] = key
                matchedUser = selectTable(db_userTableName, db_userTableColumns, whereCondition)
                if len(matchedUser) == 0:
                    return

                userBalance = float(matchedUser["BALANCE"])
                userUsableAmount = float(matchedUser["USABLE_AMOUNT"])

                setValue = {}
                setValue["BALANCE"] = userBalance + 1000
                setValue["USABLE_AMOUNT"] = userUsableAmount + 1000
                updateTable(db_userTableName, setValue, whereCondition)
            return importedBlockchain
        else:
            return None

def updateTx(blockData, id, key):
    print('\tFunction "updateTx" executed')
    phrase = re.compile(
        r"\w+[-]\w+[-]\w+[-]\w+[-]\w+")  # [6b3b3c1e-858d-4e3b-b012-8faac98b49a8]UserID hwang sent 333 bitTokens to UserID kim.
    matchList = phrase.findall(blockData.data)
    if len(matchList) == 0:
        print("No Match Found! " + str(blockData.data) + "block idx: " + str(blockData.index))
        return

    for eachuuid in matchList:
        whereCondition = {}
        whereCondition['UUID'] = eachuuid
        userData = selectTable(db_txTableName, db_txTableColumns, whereCondition)
        transferCheck = transferInfoCheck(userData['SENDER'][0], userData['RECEIVER'][0], float(userData['AMOUNT'][0]), eachuuid)

        if transferCheck == 'SUCCESS':
            setValue = {db_txTableColumns[0]: 1}
            whereCondition = {db_txTableColumns[4]: eachuuid}
            updateTable(db_txTableName, setValue, whereCondition)

    print('txData updated')


def writeTx(txRawData, senderData, inputMoney):
    print('\tFunction "writeTx" executed')
    txDataList = []
    for txDatum in txRawData:
        txList = [txDatum.commitYN, txDatum.sender, txDatum.amount, txDatum.receiver, txDatum.uuid]
        for i in range(len(txList)):
            txList[i] = str(txList[i])
        txDataList.append(txList)
    connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
    engine = create_engine(connectInfo)

    txData = selectTable(db_txTableName, db_txTableColumns)
    if (len(txData[txData['COMMIT_YN'] == '0']) >= 5):
        return -1

    newTxData = pd.DataFrame(txDataList, columns = db_txTableColumns)
    mergedTxData = pd.concat([txData, newTxData], axis=0, sort=False).reset_index(drop=True)
    replaceTable(db_txTableName, db_txTableColumns)
    try:
        to_varchar = {c: types.VARCHAR(mergedTxData[c].str.len().max()) for c in
                      mergedTxData.columns[mergedTxData.dtypes == 'object'].tolist()}
        print(to_varchar)
        mergedTxData.to_sql(db_txTableName, engine, if_exists='append', index=False, dtype=to_varchar)
    except Exception as e:
        print('Data save error, It seems to have an integrity or type problem.')
        print(e)
        to_varchar = {c: types.VARCHAR(txData[c].str.len().max()) for c in
                      txData.columns[txData.dtypes == 'object'].tolist()}
        txData.to_sql(db_txTableName, engine, if_exists='append', index=False, dtype=to_varchar)
        return 0

    setValue = {}
    setValue['USABLE_AMOUNT'] = float(senderData['USABLE_AMOUNT'][0]) - inputMoney
    whereCondition = {}
    whereCondition['USERID'] = senderData['USERID'][0]
    whereCondition['USERKEY'] = senderData['USERKEY'][0]
    updateTable(db_userTableName, setValue, whereCondition)

    print('txData written to DB')
    return 1


def readTx(tableName, columns):  # 거래내역 읽기 채굴할때 호출 블록에 없는 데이터들 불러옴
    print('\tFunction "readTx" executed')

    connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
    engine = create_engine(connectInfo)

    importedTx = []

    txReader = selectTable(tableName, columns)
    for i in range(len(txReader)):
        row = txReader.loc[i]
        if row[0] == '0':  # find unmined txData
            line = txData(row[0], row[1], row[2], row[3], row[4])
            importedTx.append(line)
    return importedTx

def getTxData():
    print('\tFunction "getTxData" executed')
    strTxData = ''
    importedTx = readTx(db_txTableName, db_txTableColumns)
    if len(importedTx) > 0:
        for i in importedTx:
            transaction = "["+ i.uuid + "]" "UserKey " + i.sender + " sent " + i.amount + " bitTokens to UserKey " + i.receiver + ". "
            print(transaction)
            strTxData += transaction
    return strTxData


def mineNewBlock(id, key, difficulty=g_difficulty, tableName=db_blockTableName, columns=db_blockTableColumns):
    print('\tFunction "mineNewBlock" executed')

    blockchain = readBlockchain(tableName, columns, id, key)
    strTxData = getTxData()
    if strTxData == '':
        print('txdata not found, so mining aborted')
        return
    timestamp = time.time()
    proof = 0
    newBlockFound = False

    print("Mining  blocks")
    while not newBlockFound:
        newBlockAttempt = generateNextBlock(blockchain, strTxData, timestamp, proof)
        if newBlockAttempt.currentHash[
           0:difficulty] == '0' * difficulty:  # 0부터 설정 난이도까지 0*4 = 0000이냐 로 묻는 것 - 즉 난이도를 만족하냐?
            stopTime = time.time()
            timer = stopTime - timestamp
            print('New block found with proof', proof, 'in', round(timer, 2), 'seconds.')
            newBlockFound = True
        else:
            print(proof)
            proof += 1

    blockchain.append(newBlockAttempt)
    writeBlockchain(blockchain, id=id, key=key, mining=True)

def mine(id, key):
    print('\tFunction "mine" executed')
    mineNewBlock(id, key)

def isSameBlock(block1, block2):
    print('\tFunction "isSameBlock" executed')
    if str(block1.index) != str(block2.index):
        return False
    elif str(block1.previousHash) != str(block2.previousHash):
        return False
    elif str(block1.timestamp) != str(block2.timestamp):
        return False
    elif str(block1.data) != str(block2.data):
        return False
    elif str(block1.currentHash) != str(block2.currentHash):
        return False
    elif str(block1.proof) != str(block2.proof):
        return False
    return True

def isValidNewBlock(newBlock, previousBlock):
    print('\tFunction "isValidNewBlock" executed')
    if int(previousBlock.index) + 1 != int(newBlock.index):
        print('Indices Do Not Match Up')
        return False
    elif previousBlock.currentHash != newBlock.previousHash:
        print("Previous hash does not match")
        return False
    elif calculateHashForBlock(newBlock) != newBlock.currentHash:
        print("Hash is invalid")
        return False
    elif newBlock.currentHash[0:g_difficulty] != '0' * g_difficulty:
        print("Hash difficulty is invalid")
        return False
    return True

def newtx(txToMining, senderData, inputMoney):
    print('\tFunction "newtx" executed')
    newtxData = []
    # transform given data to txData object
    tx = txData('0', txToMining['inputMyKey'][0], txToMining['inputMoney'][0], txToMining['inputOpponentKey'][0], uuid.uuid4())
    newtxData.append(tx)
    result = writeTx(newtxData, senderData, inputMoney)
    if result == 0:
        return 0
    elif result == -1:
        return -1
    return 1

def isValidChain(bcToValidate):
    print('\tFunction "isValidChain" executed')
    genesisBlock = []
    bcToValidateForBlock = []

    blockReader = selectTable(db_blockTableName, db_blockTableColumns)
    for i in range(len(blockReader)):
        line = blockReader.loc[i]
        block = Block(line[0], line[1], line[2], line[3], line[4], line[5])
        genesisBlock.append(block)

    # transform given data to Block object
    for line in bcToValidate:
        block = Block(line['index'], line['previousHash'], line['timestamp'], line['data'], line['currentHash'], line['proof'])
        bcToValidateForBlock.append(block)

    #if it fails to read block data  from db
    if not genesisBlock:
        print("fail to read genesisBlock")
        return False

    # compare the given data with genesisBlock
    if not isSameBlock(bcToValidateForBlock[0], genesisBlock[0]):
        print('Genesis Block Incorrect')
        return False

    for i in range(0, len(bcToValidateForBlock)):
        if isSameBlock(genesisBlock[i], bcToValidateForBlock[i]) == False:
            return False

    return True

# def addNode(queryStr):
#     print('\tFunction "addNode" executed')
#     connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
#     engine = create_engine(connectInfo)
#     # save
#     txDataList = []
#     txDataList.append([queryStr[0], queryStr[1], 0])  # ip, port, # of connection fail
#
#     nodeData = selectTable(db_nodeListTableName, db_nodeListTableColumns)
#     nodeDataList = []
#     for i in range(len(nodeData)):
#         row = nodeData.loc[i]
#         if row[0] == queryStr[0] and row[1] == queryStr[1]:
#             print("requested node is already exists")
#             return -1
#         else:
#             nodeDataList.append(row)
#
#     if (len(nodeData) > 0):
#         nodeDataFrame = pd.DataFrame(nodeDataList, columns=db_nodeListTableColumns)
#     else:
#         # this is 1st time of creating node list
#         nodeDataFrame = pd.DataFrame(txDataList, columns=db_nodeListTableColumns)
#
#     replaceTable(db_nodeListTableName, db_nodeListTableColumns)
#     try:
#         to_varchar = {c: types.VARCHAR(nodeDataFrame[c].str.len().max()) for c in
#                       nodeDataFrame.columns[nodeDataFrame.dtypes == 'object'].tolist()}
#         nodeDataFrame.to_sql(db_nodeListTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#     except:
#         print('Data save error, It seems to have an integrity or type problem.')
#         to_varchar = {c: types.VARCHAR(nodeData[c].str.len().max()) for c in
#                       nodeData.columns[nodeData.dtypes == 'object'].tolist()}
#         nodeData.to_sql(db_nodeListTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#         return 0
#
#     print('new node written to DB')
#     return 1


# def readNodes(tableName, columns):
#     print('\tFunction "readNodes" executed')
#     importedNodes = []
#
#     connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
#     engine = create_engine(connectInfo)
#
#     txReader = selectTable(tableName, columns)
#     for i in range(len(txReader)):
#         row = txReader.loc[i]
#         line = [row[0], row[1]]
#         importedNodes.append(line)
#     print("Pulling txData from DB")
#     return importedNodes

# def broadcastNewBlock(blockchain):
#     print('\tFunction "broadcastNewBlock" executed')
#     # newBlock  = getLatestBlock(blockchain) # get the latest block
#     importedNodes = readNodes(db_nodeListTableName, db_nodeListTableColumns)  # get server node ip and port
#     reqHeader = {'Content-Type': 'application/json; charset=utf-8'}
#     reqBody = []
#     nodeDataList = []
#
#     connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
#     engine = create_engine(connectInfo)
#
#     for i in blockchain:
#         reqBody.append(i.__dict__)
#
#     if len(importedNodes) > 0:
#         for node in importedNodes:
#             try:
#                 URL = "http://" + node[0] + ":" + node[1] + g_receiveNewBlock  # http://ip:port/node/receiveNewBlock
#                 res = requests.post(URL, headers=reqHeader, data=json.dumps(reqBody))
#                 if res.status_code == 200:
#                     print(URL + " sent ok.")
#                     print("Response Message " + res.text)
#                 else:
#                     print(URL + " responding error " + res.status_code)
#             except:
#                 print(URL + " is not responding.")
#                 # write responding results
#                 nodeData = selectTable(db_nodeListTableName, db_nodeListTableColumns)
#                 for i in range(len(nodeData)):
#                     row = nodeData.loc[i]
#                     if (row[0] == node[0] and row[1] == node[1]):
#                         print("connection failed " + row[0] + ":" + row[1] + ", number of fail " + row[2])
#                         tmp = row[2]
#                         # too much fail, delete node
#                         if int(tmp) > g_maximumTry:
#                             print(row[0] + ":" + row[
#                                 1] + " deleted from node list because of exceeding the request limit")
#                         else:
#                             row[2] = int(tmp) + 1
#                             nodeDataList.append(row)
#                     else:
#                         nodeDataList.append(row)
#
#                 if (len(nodeData) > 0):
#                     nodeDataFrame = pd.DataFrame(nodeDataList, columns=db_nodeListTableColumns)
#                     replaceTable(db_nodeListTableName, db_nodeListTableColumns)
#                     try:
#                         to_varchar = {c: types.VARCHAR(nodeDataFrame[c].str.len().max()) for c in
#                                       nodeDataFrame.columns[nodeDataFrame.dtypes == 'object'].tolist()}
#                         nodeDataFrame.to_sql(db_nodeListTableName, engine, if_exists='append', index=False,
#                                              dtype=to_varchar)
#                     except:
#                         print('Data save error, It seems to have an integrity or type problem.')
#                         to_varchar = {c: types.VARCHAR(nodeData[c].str.len().max()) for c in
#                                       nodeData.columns[nodeData.dtypes == 'object'].tolist()}
#                         nodeData.to_sql(db_nodeListTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#                 else:
#                     print("caught exception while updating node list")
#
# def compareMerge(bcDict):
#     print('\tFunction "compareMerge" executed')
#     heldBlock = []
#     bcToValidateForBlock = []
#
#     # Read GenesisBlock
#     connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
#     engine = create_engine(connectInfo)
#     blockReader = selectTable(db_blockTableName, db_blockTableColumns)
#     for i in range(len(blockReader)):
#         line = blockReader.loc[i]
#         block = Block(line[0], line[1], line[2], line[3], line[4], line[5])
#         heldBlock.append(block)
#
#     if len(blockReader) == 0:
#         print("file open error in compareMerge or No database exists")
#         print("call initSvr if this server has just installed")
#         return -1
#
#         # if it fails to read block data  from db
#     if len(heldBlock) == 0:
#         print("fail to read")
#         return -2
#
#     # transform given data to Block object
#     for line in bcDict:
#         # print(type(line))
#         # index, previousHash, timestamp, data, currentHash, proof
#         block = Block(line['index'], line['previousHash'], line['timestamp'], line['data'], line['currentHash'],
#                       line['proof'])
#         bcToValidateForBlock.append(block)
#
#     # compare the given data with genesisBlock
#     if not isSameBlock(bcToValidateForBlock[0], heldBlock[0]):
#         print('Genesis Block Incorrect')
#         return -1
#
#     # check if broadcasted new block,1 ahead than > last held block
#
#     if isValidNewBlock(bcToValidateForBlock[-1], heldBlock[-1]) == False:
#
#         # latest block == broadcasted last block
#         if isSameBlock(heldBlock[-1], bcToValidateForBlock[-1]) == True:
#             print('latest block == broadcasted last block, already updated')
#             return 2
#         # select longest chain
#         elif len(bcToValidateForBlock) > len(heldBlock):
#             # validation
#             if isSameBlock(heldBlock[0], bcToValidateForBlock[0]) == False:
#                 print("Block Information Incorrect #1")
#                 return -1
#             tempBlocks = [bcToValidateForBlock[0]]
#             for i in range(1, len(bcToValidateForBlock)):
#                 if isValidNewBlock(bcToValidateForBlock[i], tempBlocks[i - 1]):
#                     tempBlocks.append(bcToValidateForBlock[i])
#                 else:
#                     return -1
#             # [START] save it
#             blockchainList = []
#             for block in bcToValidateForBlock:
#                 blockList = [block.index, block.previousHash, str(block.timestamp), block.data,
#                              block.currentHash, block.proof]
#                 blockchainList.append(blockList)
#
#             blockchainData = pd.DataFrame(blockchainList, columns=db_blockTableColumns)
#             blockWriter = pd.concat([blockReader, blockchainData], axis=0, sort=False).reset_index(drop=True)
#             replaceTable(db_blockTableName, db_blockTableColumns)
#             try:
#                 to_varchar = {c: types.VARCHAR(blockWriter[c].str.len().max()) for c in
#                               blockWriter.columns[blockWriter.dtypes == 'object'].tolist()}
#                 blockWriter.to_sql(db_blockTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#             except:
#                 print('Data save error, It seems to have an integrity or type problem.')
#                 to_varchar = {c: types.VARCHAR(blockReader[c].str.len().max()) for c in
#                               blockReader.columns[blockReader.dtypes == 'object'].tolist()}
#                 blockReader.to_sql(db_blockTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#             # [END] save it
#             return 1
#         elif len(bcToValidateForBlock) < len(heldBlock):
#             tempBlocks = [bcToValidateForBlock[0]]
#             for i in range(1, len(bcToValidateForBlock)):
#                 if isValidNewBlock(bcToValidateForBlock[i], tempBlocks[i - 1]):
#                     tempBlocks.append(bcToValidateForBlock[i])
#                 else:
#                     return -1
#             print("We have a longer chain")
#             return 3
#         else:
#             print("Block Information Incorrect #2")
#             return -1
#     else:  # very normal case (ex> we have index 100 and receive index 101 ...)
#         tempBlocks = [bcToValidateForBlock[0]]
#         for i in range(1, len(bcToValidateForBlock)):
#             if isValidNewBlock(bcToValidateForBlock[i], tempBlocks[i - 1]):
#                 tempBlocks.append(bcToValidateForBlock[i])
#             else:
#                 print("Block Information Incorrect #2 " + tempBlocks.__dict__)
#                 return -1
#
#         print("new block good")
#
#         # validation
#         for i in range(0, len(heldBlock)):
#             if isSameBlock(heldBlock[i], bcToValidateForBlock[i]) == False:
#                 print("Block Information Incorrect #1")
#                 return -1
#         # [START] save it
#         blockchainList = []
#         for block in bcToValidateForBlock:
#             blockList = [block.index, block.previousHash, str(block.timestamp), block.data, block.currentHash,
#                          block.proof]
#             blockchainList.append(blockList)
#         blockchainData = pd.DataFrame(blockchainList, columns=db_blockTableColumns)
#         blockWriter = pd.concat([blockReader, blockchainData], axis=0, sort=False).reset_index(drop=True)
#         replaceTable(db_blockTableName, db_blockTableColumns)
#         try:
#             to_varchar = {c: types.VARCHAR(blockWriter[c].str.len().max()) for c in
#                           blockWriter.columns[blockWriter.dtypes == 'object'].tolist()}
#             blockWriter.to_sql(db_blockTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#         except:
#             print('Data save error, It seems to have an integrity or type problem.')
#             to_varchar = {c: types.VARCHAR(blockReader[c].str.len().max()) for c in
#                           blockReader.columns[blockReader.dtypes == 'object'].tolist()}
#             blockReader.to_sql(db_blockTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#         # [END] save it
#         return 1

# def initSvr():
#     print('\tFunction "initSvr" executed')
#     connectInfo = 'oracle+cx_oracle://%s:%s@%s:%s/%s' % (db_id, db_pw, db_ip, db_port, db_serviceName)
#     engine = create_engine(connectInfo)
#     last_line_number = len(selectTable(db_nodeListTableName, db_nodeListTableColumns))
#     # 1. check if we have a node list file
#     # if we don't have, let's request node list
#     if last_line_number == 0:
#         # get nodes...
#         for key, value in g_nodeList.items():
#             URL = 'http://' + key + ':' + value + '/node/getNode'
#             try:
#                 res = requests.get(URL)
#             except requests.exceptions.ConnectionError:
#                 continue
#
#             if res.status_code == 200:
#                 print(res.text)
#                 tmpNodeLists = json.loads(res.text)
#                 for node in tmpNodeLists:
#                     addNode(node)
#     # 2. check if we have a blockchain data file
#     last_line_number = len(selectTable(db_blockTableName, db_blockTableColumns))
#     blockchainList = []
#     if last_line_number == 0:
#         # get Block Data...
#         for key, value in g_nodeList.items():
#             URL = 'http://' + key + ':' + value + '/block/getBlockData'
#             try:
#                 res = requests.get(URL)
#             except requests.exceptions.ConnectionError:
#                 continue
#             if res.status_code == 200:
#                 print(res.text)
#                 tmpbcData = json.loads(res.text)
#                 for line in tmpbcData:
#                     # print(type(line))
#                     # index, previousHash, timestamp, data, currentHash, proof
#                     block = [line['index'], line['previousHash'], line['timestamp'], line['data'], line['currentHash'],
#                              line['proof']]
#                     blockchainList.append(block)
#
#                 blockchainData = pd.DataFrame(blockchainList, columns=db_blockTableColumns)
#                 replaceTable(db_blockTableName, db_blockTableColumns)
#                 try:
#                     to_varchar = {c: types.VARCHAR(blockchainData[c].str.len().max()) for c in
#                                   blockchainData.columns[blockchainData.dtypes == 'object'].tolist()}
#                     blockchainData.to_sql(db_blockTableName, engine, if_exists='append', index=False, dtype=to_varchar)
#                 except Exception as e:
#                     print('Data save error in initSvr()', e)
#     return 1


class myHandler(BaseHTTPRequestHandler):

    #def __init__(self, request, client_address, server):
    #    BaseHTTPRequestHandler.__init__(self, request, client_address, server)

    # Handler for the GET requests
    def do_GET(self):
        data = []  # response json data
        userKey = 0
        if None != re.search('/id', self.path):
            recordID = self.path.split('?')[-1]
            userId = recordID.split('=')[-1]
            checkError = selectTable(db_userTableName, db_userTableColumns)
            del checkError

            isSuccess = False
            for i in range(100):
                keyTemp = str(randint(0, 10000000))  # 키값을 난수로 생성
                userKey = keyTemp.zfill(10)  # 키 자릿수를 10자리로 맞춰줌
                if insertData(db_userTableName, USERID=userId, USERKEY=userKey, BALANCE='0', USABLE_AMMONT='0'):
                    isSuccess = True

                    break
            if isSuccess == False:
                print("USERKEY INSERT ERROR")
                return

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # self.wfile.write(bytes("SUCCESS", 'utf-8'))
            self.wfile.write(bytes(userKey, 'utf-8'))
            return

        elif None != re.search('/login', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            path = './html_files/login.html'
            f = codecs.open(path, 'r', encoding='utf-8').read()
            self.wfile.write(bytes(f, 'utf-8'))

        elif None != re.search('/tx', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            path = './html_files/tx.html'
            f = codecs.open(path, 'r', encoding='utf-8').read()
            self.wfile.write(bytes(f, 'utf-8'))

        elif None != re.search('/mine', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            path = './html_files/mine.html'
            f = codecs.open(path, 'r', encoding='utf-8').read()
            self.wfile.write(bytes(f, 'utf-8'))

        elif None != re.search('/block/*', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            # 약점 : 사이즈가 커서 한번에 주면 서버가 죽을 수 있다. 나눠서 줘야함( 페이징 처리 / 게시물의 범위 )
            if None != re.search('/block/getBlockData', self.path):
                # queryString = urlparse(self.path).query.split('&')

                block = readBlockchain(db_blockTableName, db_blockTableColumns, mode='external')
                try:
                    if len(block) == 0 :
                        data.append("no data exists")
                    else :
                        for i in block:
                            print(i.__dict__)
                            data.append(i.__dict__)
                except:
                    data.append("no data exists")

                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

            elif None != re.search('/block/generateBlock', self.path):
                global count2
                if (count2 > 0):
                    self.wfile.write(bytes(json.dumps({'SUCCESS': 'MANY_REQUEST'}), "utf-8"))
                    return
                count2 += 1
                if None != re.search('/block/generateBlock\?id=[\w]+&key=[\d]{10}', self.path):
                    parameter = self.path.split('?')[-1]
                    id = parameter.split('&')[0]
                    if (id.split('=')[0] == 'id'):
                        id = id.split('=')[1]
                    else:
                        self.wfile.write(bytes(json.dumps({'SUCCESS': 'URL_PROBLEM'}, sort_keys = True, indent = 4), "utf-8"))
                        count2 = 0
                        return
                    key = parameter.split('&')[1]
                    if (key.split('=')[0] == 'key'):
                        key = key.split('=')[1]
                    else:
                        self.wfile.write(bytes(json.dumps({'SUCCESS': 'URL_PROBLEM'}, sort_keys = True, indent = 4), "utf-8"))
                        count2 = 0
                        return
                else:
                    self.wfile.write(bytes(json.dumps({'SUCCESS': 'URL_PROBLEM'}, sort_keys=True, indent=4), "utf-8"))
                    count2 = 0
                    return

                whereCondition = {}
                whereCondition["USERID"] = id
                whereCondition["USERKEY"] = key
                matchedUser = selectTable(db_userTableName, db_userTableColumns, whereCondition)
                if len(matchedUser) == 0:
                    self.wfile.write(bytes(json.dumps({'SUCCESS': 'NO_MATCH'}, sort_keys=True, indent=4), "utf-8"))
                    count2 = 0
                    return
                t = mine(id, key)
                count2 = 0
                self.wfile.write(bytes(json.dumps({'SUCCESS': 'MATCH'}, sort_keys=True, indent=4), "utf-8"))
            else:
                data.append("{info:no such api}")
                self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

            # elif None != re.search('/node/*', self.path):
            #     self.send_response(200)
            #     self.send_header('Content-type', 'application/json')
            #     self.end_headers()
            #     if None != re.search('/node/addNode', self.path):
            #         queryStr = urlparse(self.path).query.split(':')
            #         print("client ip : "+self.client_address[0]+" query ip : "+queryStr[0])
            #         if self.client_address[0] != queryStr[0]:
            #             data.append("your ip address doesn't match with the requested parameter")
            #         else:
            #             res = addNode(queryStr)
            #             if res == 1:
            #                 importedNodes = readNodes(db_nodeListTableName, db_nodeListTableColumns)
            #                 data = importedNodes
            #                 print("node added okay")
            #             elif res == 0 :
            #                 data.append("caught exception while saving")
            #             elif res == -1 :
            #                 importedNodes = readNodes(db_nodeListTableName, db_nodeListTableColumns)
            #                 data = importedNodes
            #                 data.append("requested node is already exists")
            #         self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))
            #     elif None != re.search('/node/getNode', self.path):
            #         importedNodes = readNodes(db_nodeListTableName, db_nodeListTableColumns)
            #         data = importedNodes
            #         self.wfile.write(bytes(json.dumps(data, sort_keys=True, indent=4), "utf-8"))

        elif None != re.search('/', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            path = './html_files/blockchainHome.html'
            f = codecs.open(path, 'r', encoding='utf-8').read()
            self.wfile.write(bytes(f, 'utf-8'))

        else:
            if None != re.search('favicon.ico', self.path):
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                return
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        # ref : https://mafayyaz.wordpress.com/2013/02/08/writing-simple-http-server-in-python-with-rest-and-json/

    def do_POST(self):
        if None != re.search('/tx_data', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            global count
            if (count > 0):
                self.wfile.write(bytes(json.dumps({'SUCCESS':'MANY_REQUEST'}), "utf-8"))
                return

            count += 1
            ctype, pdict = cgi.parse_header(self.headers['content-type'])  # cgi기억하기 : cgi라는 모듈은 들어오는 모든 확장자를 받아주는(?)모듈
            print(ctype)
            print(pdict)

            if ctype == 'application/x-www-form-urlencoded':
                content_length = int(self.headers['Content-Length'])
                postvars = parse_qs((self.rfile.read(content_length)).decode('utf-8'), keep_blank_values=True)
                print(postvars)  # print(type(postvars)) #print(postvars.keys())

                if postvars['inputMyID'][0] == '':
                    postvars['SUCCESS'] = "FAILED"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return
                elif postvars['inputMyKey'][0] == '':
                    postvars['SUCCESS'] = "FAILED"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return
                elif postvars['inputOpponentID'][0] == '':
                    postvars['SUCCESS'] = "FAILED"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return
                elif postvars['inputOpponentKey'][0] == '':
                    postvars['SUCCESS'] = "FAILED"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return
                elif postvars['inputMoney'][0] == '':
                    postvars['SUCCESS'] = "FAILED"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return

                try:
                    inputMoney = float(postvars['inputMoney'][0])
                except:
                    postvars['SUCCESS'] = "NUMBER"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return

                whereCondition = {}
                whereCondition['USERID'] = postvars['inputMyID'][0]
                whereCondition['USERKEY'] = postvars['inputMyKey'][0]
                senderData = selectTable(db_userTableName, db_userTableColumns, whereCondition)
                if (len(senderData) == 0):
                    postvars['SUCCESS'] = "NO_MATCH_SENDER"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return

                whereCondition = {}
                whereCondition['USERID'] = postvars['inputOpponentID'][0]
                whereCondition['USERKEY'] = postvars['inputOpponentKey'][0]
                receiverData = selectTable(db_userTableName, db_userTableColumns, whereCondition)
                if (len(receiverData) == 0):
                    postvars['SUCCESS'] = "NO_MATCH_RECEIVER"
                    self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                    return

                if (float(senderData['USABLE_AMOUNT'][0]) >= inputMoney) and inputMoney > 0:
                    pass
                else:
                    if (inputMoney <= 0):
                        postvars['SUCCESS'] = "ZERO_ENTERED"
                        self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                        return
                    else:
                        postvars['SUCCESS'] = "LACK_OF_USABLE_AMOUNT"
                        postvars['USABLE'] = senderData['USABLE_AMOUNT'][0]
                        self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                        return

                res = newtx(postvars, senderData, inputMoney)
                if res == 1:
                    postvars["SUCCESS"] = "ACCEPTED"
                elif res == -1:
                    postvars["SUCCESS"] = "MINE_BLOCK"
                else:
                    postvars["SUCCESS"] = "ERROR"

                self.wfile.write(bytes(json.dumps(postvars), "utf-8"))
                count = 0
                return

            else:
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
        if None != re.search('/check_amount', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            ctype, pdict = cgi.parse_header(self.headers['content-type'])  # cgi기억하기 : cgi라는 모듈은 들어오는 모든 확장자를 받아주는(?)모듈
            print(ctype)
            print(pdict)

            if ctype == 'application/x-www-form-urlencoded':  # application/json은? => 컨텐츠타입
                content_length = int(self.headers['Content-Length'])
                checkAmount = parse_qs((self.rfile.read(content_length)).decode('utf-8'), keep_blank_values=True)
                print(checkAmount)

                if checkAmount['key'][0] == '':
                    checkAmount['SUCCESS'] = "FAILED"
                    self.wfile.write(bytes(json.dumps(checkAmount), "utf-8"))
                    return

                try:
                    key = float(checkAmount['key'][0])
                except:
                    checkAmount['SUCCESS'] = "NUMBER"
                    self.wfile.write(bytes(json.dumps(checkAmount), "utf-8"))
                    return

                whereCondition = {}

                whereCondition['USERKEY'] = checkAmount['key'][0]
                senderData = selectTable(db_userTableName, db_userTableColumns, whereCondition)
                if (len(senderData) == 0):
                    checkAmount['SUCCESS'] = "NO_MATCH_KEY"
                    self.wfile.write(bytes(json.dumps(checkAmount), "utf-8"))
                    return

                checkAmount['SUCCESS'] = "AMOUNT_CHECK"
                checkAmount['USABLE_AMOUNT'] = senderData['USABLE_AMOUNT'][0]
                checkAmount['BALANCE'] = senderData['BALANCE'][0]
                self.wfile.write(bytes(json.dumps(checkAmount), "utf-8"))
                return

            else:
                self.send_response(403)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

        elif None != re.search('/block/*', self.path):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            if None != re.search('/block/validateBlock/*', self.path):
                ctype, pdict = cgi.parse_header(self.headers['content-type'])
                #print(ctype) #print(pdict)

                if ctype == 'application/json':
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    receivedData = post_data.decode('utf-8')
                    print(type(receivedData))
                    tempDict = json.loads(receivedData)  # load your str into a list #print(type(tempDict))
                    if isValidChain(tempDict) == True :
                        tempDict.append("validationResult:normal")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
                    else :
                        tempDict.append("validationResult:abnormal")
                        self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))

        # elif None != re.search('/node/*', self.path):
        #     self.send_response(200)
        #     self.send_header('Content-type', 'application/json')
        #     self.end_headers()
        #     if None != re.search(g_receiveNewBlock, self.path): # /node/receiveNewBlock
        #         content_length = int(self.headers['Content-Length'])
        #         post_data = self.rfile.read(content_length)
        #         receivedData = post_data.decode('utf-8')
        #         tempDict = json.loads(receivedData)  # load your str into a list
        #         print(tempDict)
        #         res = compareMerge(tempDict)
        #         if res == -1: # internal error
        #             tempDict.append("internal server error")
        #         elif res == -2 : # block chain info incorrect
        #             tempDict.append("block chain info incorrect")
        #         elif res == 1: #normal
        #             tempDict.append("accepted")
        #         elif res == 2: # identical
        #             tempDict.append("already updated")
        #         elif res == 3: # we have a longer chain
        #             tempDict.append("we have a longer chain")
        #         self.wfile.write(bytes(json.dumps(tempDict), "utf-8"))
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

try:

    # Create a web server and define the handler to manage the
    # incoming request
    # server = HTTPServer(('', PORT_NUMBER), myHandler)
    server = ThreadedHTTPServer(('', PORT_NUMBER), myHandler)
    print('Started httpserver on port ', PORT_NUMBER)

    # initSvr()
    # Wait forever for incoming http requests
    server.serve_forever()

except KeyboardInterrupt as e:
    print('^C received, shutting down the web server')
    print(e)
    server.socket.close()

except Exception as e:
    print('Error')
    print(e)
    server.socket.close()