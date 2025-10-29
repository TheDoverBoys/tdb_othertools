import sys

def everything(file):
    conso_lookup = [0x1100, 0x3132, 0x3134, 0x3137, 0x3138, 0x3139, 0x3141, 0x3142, 0x3143, 0x3145, 0x3146, 0x3147, 0x3148, 0x3149, 0x314a, 0x314b, 0x314c, 0x314d, 0x314e]
    vowel_lookup = [0x06, 0x08, 0x0A, 0x0C, 0x0E, 0x14, 0x16, 0x18, 0x1A, 0x1C, 0x1E, 0x24, 0x26, 0x28, 0x2A, 0x2C, 0x2E, 0x34, 0x36, 0x38, 0x3A]
    fileData = file.read()
    textContents = open("output.txt","wb")
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
                    char = 0xAC00 + (0x024C * consonantOne) + (0x1C * vowel_lookup.index(vowel)) + (consonantTwo-1-(consonantTwo//0x12))
                textContents.write(char.to_bytes(2, byteorder='big'))
                if fileData[i+1] == 0x00:
                    textContents.write("\n".encode("utf-16-be"))
                flag = True
            elif fileData[i] == 0x00:
                textContents.write("\n".encode("utf-16-be"))
            else:
                pass

if __name__ == "__main__":
    try:
        file = sys.argv[1]
    except IndexError as e:
        raise Exception("The files are not there") from e
    everything(open(file, "rb"))