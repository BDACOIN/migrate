
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
    print("Retrieving page", page)
    return BeautifulSoup(sess.get(url).text, 'html.parser')

def getPage(sess, page):
    table = getData(sess, str(int(page))).find('table')
    return [[X.text.strip() for X in row.find_all('td')] for row in table.find_all('tr')]

# 外部が参照するデータ
externalHoldersRatioData = {}

# 今蓄積してる最中のデータ
internalHoldersRatioData = {}

def FilterMasterWallet(address: str) -> str:
    target = "0x89c9F8700e978FB87AD5Cc159B14E380F8E70352"
    if address.upper() == target.upper():
        return address + " (BDA NEW Master Wallet)"
    return address

def FilterOldMasterWallet(address: str) -> str:
    target = "0x25862c0a85a635e1972d3c4f47d909bc71fe4659"
    if address.upper() == target.upper():
        return address + " (BDA Old Master Wallet)"
    return address

def FilterUzurasWallet(address: str) -> str:
    target = "0x5ff15142cf8f34e917364674165bc2c69b3ae9f3"
    if address.upper() == target.upper():
        return address + " (UZURAS Wallet)"
    return address

def FilterPresaleFullWallet(address: str) -> str:
    target = [ "0x494Da578D0470A2E43B8668826De87e6BC74bECf", "0xc2ed388c5255155014C81aD8834850Fe63d00306", "0x288652040352D542A1Ec0d5Ce4c7be266FE82b1f",  "0xed1C69B9c08602c75A576c6Bd0cE602f9CbF838F"]
    target = list(map(lambda s: s.upper(), target))
    if address.upper() in target:
        return address + " (Presale Full Wallet)"
    return address

def FilterPresaleHalfWallet(address: str) -> str:
    target = "0xFc901d07884095C3D8d2FEa42c392BA8468b63a1"
    if address.upper() == target.upper():
        return address + " (Presale Half Wallet)"
    return address

def FilterPresaleMicroWallet(address: str) -> str:
    target = "0x7607aEDB36183DEb0474037B8783f31d2026a36f"
    if address.upper() == target.upper():
        return address + " (Presale Micro Wallet)"
    return address


async def ReCalculateHoldersRatio():
    global externalHoldersRatioData
    global internalHoldersRatioData

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
            d[1] = FilterMasterWallet(d[1])
            d[1] = FilterOldMasterWallet(d[1])
            d[1] = FilterUzurasWallet(d[1])
            d[1] = FilterPresaleFullWallet(d[1])
            d[1] = FilterPresaleHalfWallet(d[1])
            d[1] = FilterPresaleMicroWallet(d[1])
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


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(ReCalculateHoldersRatio())
    print(results)
    pprint.pprint(externalHoldersRatioData)
