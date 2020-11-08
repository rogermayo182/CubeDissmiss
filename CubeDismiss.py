import os
import pandas as pd
import numpy as np
#import cv2
import sys
import time

sys.setrecursionlimit(1000000)
gGameSqureNum = 5

#全局变量
class GlobalData:
    calcScore = 0
    bestScore = 0
    def __init__(self):
        calcScore = 0

#read the screenshot image,identify the color,map to the data table
def initData(file_name):
    cur_dir = r"E:\Work\screenshot"
    file_path = cur_dir + '\\' + file_name

    pic = os.path.exists(file_path)
    # image = cv2.imread(pic)

    #TODO covert image to dataMap
    # dataMap = np.zeros(100).reshape(10,10)
    dataMap = np.random.randint(1,6,(gGameSqureNum,gGameSqureNum))
    # n =  [[3, 4, 4, 3], [3, 2, 2, 2], [2, 3, 4, 2], [2, 4, 2, 1]]
    # n=[[3,3,3,1],
    #  [2,2,2,2]
    # ,[2,4,3,1],
    #  [4,3,4,1]]
    # dataMap =np.array(n)


    return dataMap

def priorHandleCa(nd):
    data = nd.DataMap
    boundary = gGameSqureNum -1
    target = pd.DataFrame(np.zeros(gGameSqureNum*gGameSqureNum).reshape(gGameSqureNum,gGameSqureNum))
    for i in range(gGameSqureNum):
        for j in range(gGameSqureNum):
            if data.iloc[i,j] == -1:
                # 已经消掉的处理
                continue
            if j < boundary and data.iloc[i,j] == data.iloc[i,j+1]:
                target.iloc[i,j] = 1
                target.iloc[i,j+1] = 1
            if i < boundary and data.iloc[i,j] == data.iloc[i+1,j]:
                target.iloc[i,j] = 1
                target.iloc[i+1,j] = 1

    return data * target

def PriorHandle(nd):

    data = nd.DataMap
    lastRow = gGameSqureNum - 1
    afterRow = data.drop(0)
    afterRow.index = range(lastRow)
    afterRow = data - afterRow
    afterRow = afterRow[afterRow == 0].fillna(1)

    beforeRow = data.drop(lastRow)
    beforeRow.index = range(1,lastRow+1)
    beforeRow = beforeRow - data
    beforeRow = beforeRow[beforeRow ==0].fillna(1)

    combineRow = afterRow + beforeRow
    combineRow[combineRow!=2] = 0
    RowMode = data[combineRow==0].fillna(0)

    afterColumn = data.drop(0,1)
    afterColumn.rename(columns=lambda x: x-1, inplace=True)
    afterColumn = data - afterColumn
    afterColumn = afterColumn[afterColumn == 0].fillna(1)

    beforeColumn = data.drop(gGameSqureNum - 1,1)
    beforeColumn.rename(columns=lambda x: x+1,inplace=True)
    beforeColumn = beforeColumn - data
    beforeColumn = beforeColumn[beforeColumn ==0].fillna(1)
    ColumnMode = afterColumn + beforeColumn
    ColumnMode[ColumnMode != 2] = 0
    ColumnMode = data[ColumnMode==0].fillna(0)

    #print(data)
    #print(RowMode)
    #print(ColumnMode)

    tmp = RowMode - ColumnMode

    #check two table

    #print(((tmp==0).sum(axis=1)).sum())

    ColumnMode[tmp == 0.0] = 0

    totalMode = RowMode + ColumnMode

    return totalMode


#单个可消除图形信息
class patNode:
    # index=0  #the index of connect pattern in this image
    # posList = []
    def __init__(self):
        self.index = 0
        self.id = 0   #color value
        #self.score = 0  
        self.num = 0     #connect cube number
        self.posList = []

# 用于存储当前画面的所有可消除图形信息
class sNodeInfo:
    # cubeRecoder = []
    def __init__(self, data):
        self.DataMap = pd.DataFrame(data, index=range(gGameSqureNum), columns=range(gGameSqureNum))
        self.cubeRecoder = []
        self.scoreTotal = 0

    # def addNode(ni):
    #     cubeRecoder.append(ni)

def SearchLink(srcset,srclist):
    data_set = set()
    for m in srcset:
        # data_set.add(m)
        srclist.remove(m)
        for z in srclist:
            res = np.abs(m - z)
            # (1<<8)
            if res == 1 or res == 256:
            # if res == 1 or res == 100:
                data_set.add(z)

    if len(data_set)> 0:
        #TODO 将srclist中的data_set值去掉
        prores = SearchLink(data_set,srclist)
        return srcset | prores
    else:
        return srcset

def FindPattern(RawData):

    #用于记录本论的信息
    nodeData = sNodeInfo(RawData)
    nodeIndex = 0
    
    #预处理
    # prioData = PriorHandle(nodeData)
    prioData = priorHandleCa(nodeData)

    cubeID = [1,2,3,4,5]  # different color
    selectList = [[],[],[],[],[]]

    for i in range(gGameSqureNum):
        for j in range(gGameSqureNum):
            value = int(prioData.iloc[i, j])
            if value > 0:
                # selectList[value - 1].append(i * 100 + j)
                selectList[value - 1].append((i << 8) + j)

    for n in cubeID:
        if len(selectList[n-1]) <= 0:
            #如果没有值，直接下一个颜色
            continue
        tmpList = selectList[n-1]
        while len(tmpList) > 0:
            input = {tmpList[0]}
            res = SearchLink(input, tmpList)
            if res != input:
                pn = patNode()
                pn.posList = list(res)
                pn.id = n
                pn.index = nodeIndex
                pn.num = len(res)
                nodeIndex += 1
                # nodeData.addNode(pn)
                nodeData.cubeRecoder.append(pn)
            else:
                # 继续找下一个
                continue

    return nodeData           
      
def TrigerAction(ndRecoder, srcData):
    rawData = srcData.copy()
    score = ndRecoder.num * ndRecoder.num
    columnRecSet = set()

    ndRecoder.posList.sort()
    for n in ndRecoder.posList:
        # row = int(n / 100)
        # column = int(n % 100)
        row = int(n) >> 8
        column = int(n & 0xff)
        columnRecSet.add(column)
        # 倒减
        for i in range(int(row), 0, -1):
            rawData.iloc[i, column] = rawData.iloc[i - 1, column]

        # 最上面添加-1
        rawData.iloc[0, column] = -1

    columnRecList = list(columnRecSet)
    columnRecList.sort(reverse=True)

    # 所有行消除完了后，检查整行没有了的，右边的左移，必须先移动列数大的
    for rec_column in columnRecList:
        # 如果整列为-1
        # if (rawData[rec_column] == -1).all():
        if (rawData[rec_column] != -1).any() == False:
            rawData[gGameSqureNum] = -1
            rawData.drop(rec_column, axis=1, inplace=True )
            rawData.rename(columns=lambda x:x-1 if x > rec_column else x, inplace=True)

    return rawData, score


x = 0
gTopScorePath = []
gTmpScorePath = []
gHighestScore = 0


def CheckCycle(data,presocre):
    # while True:
    global x
    global gHighestScore
    global gTmpScorePath
    global gTopScorePath

    gTmpScorePath.append(data)
    nd = FindPattern(data)
    # lengthNode = len(nd.cubeRecoder)
    # print(lengthNode)
    if len(nd.cubeRecoder) <= 0:
        # return nd.scoreTotal
        # print("end")
        # print(presocre)
        if presocre > gHighestScore:
            gHighestScore = presocre
            gTopScorePath = gTmpScorePath.copy()
            # return
        # else:
            # gTmpScorePath.clear()
        gTmpScorePath.pop()
        return

    nd.scoreTotal = presocre

    for n in nd.cubeRecoder:
        outData, score = TrigerAction(n, nd.DataMap)

        # print(outData)
        x += 1
        # print(x)
        nextscore = presocre + score

        # setup the table
        res = CheckCycle(outData, nextscore)

    # 本层级没有可以消除的了
    gTmpScorePath.pop()

if __name__ ==  '__main__':
    RawData = initData(r"screenshot.jpg")
    print(RawData)
    start = time.time()

    checkRes = CheckCycle(RawData,0)

    for n in gTopScorePath:
        print(n)
        print("")
    print(gHighestScore)
    print(x)

    end = time.time()
    print("__main__ use time %s" % (end - start))
   
    


