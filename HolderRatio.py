
from __future__ import print_function
import os
import requests
from bs4 import BeautifulSoup
import csv
import time
import pprint
import copy
import asyncio

# 全ホルダーの枚数や順位、比率バランスを辞書で得る
# BurnやらMintやらCollectTokenやら、入り混じっていて、イベント記録を集めて枚数出すのは危ないので
# etherscanのホルダー結果をそのまま格納していく。

CONTRACT_ADD = "0xF6CaA4bebD8Fab8489bC4708344d9634315c4340" # BDA v1.0
HOLDERS_URL = "https://etherscan.io/token/generic-tokenholders2?a={}&s=0&p=".format(CONTRACT_ADD)

def getData(sess, page):
    url = HOLDERS_URL + page
    # print("Retrieving page", page)
    return BeautifulSoup(sess.get(url).text, 'html.parser')

def getPage(sess, page):
    table = getData(sess, str(int(page))).find('table')
    return [[X.text.strip() for X in row.find_all('td')] for row in table.find_all('tr')]


def filterMasterWallet(address: str) -> str:
    target = "0x89c9F8700e978FB87AD5Cc159B14E380F8E70352"
    if address.upper() == target.upper():
        return address + " (BDA NEW Master Wallet)"
    return address

def filterOldMasterWallet(address: str) -> str:
    target = "0x25862c0a85a635e1972d3c4f47d909bc71fe4659"
    if address.upper() == target.upper():
        return address + " (BDA Old Master Wallet)"
    return address

def filterOldPoolWallet(address: str) -> str:
    target = "0x4da8a2fd6af6e9305fbe1ade05dc224ae0fe7fde"
    if address.upper() == target.upper():
        return address + " (BDA Old Pool Wallet)"
    return address


def filterUzurasWallet(address: str) -> str:
    target = "0x5ff15142cf8f34e917364674165bc2c69b3ae9f3"
    if address.upper() == target.upper():
        return address + " (UZURAS Wallet)"
    return address

def filterPresaleFullWallet(address: str) -> str:
    target = [ "0x494Da578D0470A2E43B8668826De87e6BC74bECf", "0xc2ed388c5255155014C81aD8834850Fe63d00306", "0x288652040352D542A1Ec0d5Ce4c7be266FE82b1f",  "0xed1C69B9c08602c75A576c6Bd0cE602f9CbF838F"]
    target = list(map(lambda s: s.upper(), target))
    if address.upper() in target:
        return address + " (Presale Full Wallet)"
    return address

def filterPresaleHalfWallet(address: str) -> str:
    target = "0xFc901d07884095C3D8d2FEa42c392BA8468b63a1"
    if address.upper() == target.upper():
        return address + " (Presale Half Wallet)"
    return address

def filterPresaleMicroWallet(address: str) -> str:
    target = "0x7607aEDB36183DEb0474037B8783f31d2026a36f"
    if address.upper() == target.upper():
        return address + " (Presale Micro Wallet)"
    return address

# 外部が参照するデータ
externalHoldersRatioData = {}

# 外部が参照するデータ
externalSpecialHoldersRatioData = {}

# 今蓄積してる最中のデータ
internalHoldersRatioData = {}

# 特別
internalSpecialHoldersRatioData = {}


async def reCalculateHoldersRatio():
    global externalHoldersRatioData
    global externalSpecialHoldersRatioData
    global internalHoldersRatioData
    global internalSpecialHoldersRatioData

    resp = requests.get(HOLDERS_URL)
    sess = requests.Session()

    page = 0
    while True:
        page += 1
        data = getPage(sess, page)
        print(str(data))
        print(len(data))

        # 有効なデータが１つでもあるか
        data_exist = False
        for d in data:
            if len(d) < 4:
                continue

            d[2] = d[2].replace(",", "") # 文字列中に、桁数を見やすくする際に入ってる「,」を除去
            # internalHoldersRatioData[ d[1] ] = [ d[0], d[2], d[3] ]
            d[1] = filterMasterWallet(d[1])
            d[1] = filterOldMasterWallet(d[1])
            d[1] = filterOldPoolWallet(d[1])
            d[1] = filterUzurasWallet(d[1])
            d[1] = filterPresaleFullWallet(d[1])
            d[1] = filterPresaleHalfWallet(d[1])
            d[1] = filterPresaleMicroWallet(d[1])

            # 空白入ってるなら特別
            if " " in d[1]:
                internalSpecialHoldersRatioData[ d[1] ] = float(d[2])
            else:
                internalHoldersRatioData[ d[1] ] = float(d[2])

            # 有効なデータがあった
            data_exist = True

        # 有効なデータが１つもないのであれば、それ以降みても無駄である。
        if not data_exist:
            break

        # あまり連続でアクセスしすぎるとSPAM認定されかねないので、間隔をあける
        await asyncio.sleep(2)

    # 外部が参照するデータへと書き込み。
    # 時間をかけてデータを蓄積しているため、このようにすべてを蓄積しおえた
    # タイミングで上書きする。
    externalHoldersRatioData = copy.deepcopy(internalHoldersRatioData)
    externalSpecialHoldersRatioData = copy.deepcopy(internalSpecialHoldersRatioData)


def printNormalDistributeAttribute():
    tempaddress = []
    tempamounts = []
    for address in externalHoldersRatioData.keys():
        tempaddress.append(address)
        tempamounts.append(externalHoldersRatioData[address])

        if len(tempaddress) >= 18:
            print(tempaddress)
            print("-------------------------------------\n")
            print(tempamounts)
            print("=====================================\n\n")

            tempaddress.clear()
            tempamounts.clear()

    if len(tempaddress):
        print(tempaddress)
        print("-------------------------------------\n")
        print(tempamounts)
        print("=====================================\n\n")


def printSpecialDistributeAttribute():
    print ("先行フリーズ対象")
    print ( ['0x5ff15142cf8f34e917364674165bc2c69b3ae9f3', '0x288652040352d542a1ec0d5ce4c7be266fe82b1f', '0xc2ed388c5255155014c81ad8834850fe63d00306', '0xed1c69b9c08602c75a576c6bd0ce602f9cbf838f', '0xfc901d07884095c3d8d2fea42c392ba8468b63a1' ] )
    print("-------------------------------------\n")
    pprint.pprint(externalSpecialHoldersRatioData)
    print("=====================================\n\n")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(reCalculateHoldersRatio())
    print(results)

    printSpecialDistributeAttribute()
    printNormalDistributeAttribute()

    # pprint.pprint(externalHoldersRatioData)
