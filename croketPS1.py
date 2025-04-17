import os, math

def everything(file, table):
    fileData = file.read()
    tableData = table.read()
    tableEntry = 13
    fileSegment = 2048
    fileTable = []
    for i in range(len(tableData)//tableEntry):
        fileName = str(tableData[i*tableEntry:8+(i*tableEntry)].decode())
        fileFormat = str(tableData[8+(i*tableEntry):10+(i*tableEntry)].decode())
        fileLength = int.from_bytes(tableData[10+(i*tableEntry):13+(i*tableEntry)], "big")
        fileTable.append([fileName, fileFormat, fileLength])
        #print(fileTable[i])
    
    curOffset = 0
    #extractLog = open("log.txt","w")
    fileDir = './extracted/'
    if not os.path.isdir(fileDir):
        os.mkdir(fileDir)
    for i in range(len(tableData)//tableEntry):
        fileName = fileTable[i][0] + "." + fileTable[i][1]
        filePath = os.path.join(fileDir, fileName)
        fileLength = fileTable[i][2]
        extractFile = open(filePath,"wb")
        if curOffset % fileSegment:
            curOffset = int(math.ceil(curOffset/fileSegment)*fileSegment)
        extractFile.write(fileData[curOffset:curOffset+fileLength])
        #extractLog.write(fileName + " " + str(curOffset) + " " + '\n')
        extractFile.close()
        curOffset += fileLength
    #extractLog.close()

if __name__ == "__main__":
    try:
        referenceFile = open('BIND.DAT',"rb")
        tableFile = open('BIND.TBL',"rb")
    except IndexError:
        print("The files are not here")
        exit()
    everything(referenceFile, tableFile)