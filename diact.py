import sys

def everything(file, output):
    if output is None:
        output = (file + "_output.txt")
    conso_lookup = [0x1100, 0x3132, 0x3134, 0x3137, 0x3138, 0x3139, 0x3141, 0x3142, 0x3143, 0x3145, 0x3146, 0x3147, 0x3148, 0x3149, 0x314a, 0x314b, 0x314c, 0x314d, 0x314e]
    fileData = open(file, "rb").read()
    textContents = open(output,"wb")
    flag = False
    textContents.write(0xFEFF.to_bytes(2, byteorder='big'))
    for i in range(len(fileData)):
        if flag:
            flag = False
        else:
            if fileData[i] < 0x88 and fileData[i] >= 0x20:
                textContents.write(fileData[i].to_bytes(2, byteorder='big'))
            elif fileData[i] >= 0x88 and fileData[i] < 0xD4:
                consonantOne = (fileData[i]-0x88)//4
                vowel = (((fileData[i]&0x0F)%0x04)<<4)+(((fileData[i+1]>>4)//2)*2)
                consonantTwo = fileData[i+1]%0x20
                if vowel < 0x06 or (vowel >= 0x06 and vowel%0x10 < 0x04) or vowel > 0x3A or fileData[i+1] == 0x00:
                    char = conso_lookup[consonantOne]
                else:
                    char = 0xAC00 + (0x024C * consonantOne) + (0x1C * ((vowel//2)-3-((vowel//0x10)*2))) + (consonantTwo-1-(consonantTwo//0x12))
                textContents.write(char.to_bytes(2, byteorder='big'))
                if fileData[i+1] == 0x00:
                    textContents.write("\n".encode("utf-16-be"))
                flag = True
            elif fileData[i] == 0x00:
                textContents.write("\n".encode("utf-16-be"))
            else:
                pass
    textContents.close()

if __name__ == "__main__":
    try:
        file = sys.argv[1]
    except IndexError as e:
        raise Exception("The files are not there") from e
    try:
        output = sys.argv[2]
    except:
        output = None
    everything(file, output)