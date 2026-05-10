import sys, os, re

class IIDX6Decrypt:
    def __init__(self, data, output):
        self.data = data
        __counters = self.separateBytes(self.data)
        __evenstart = self.evenfrequency(__counters[0])
        __key = self.generateKey(__evenstart, len(self.data))
        for i in range(len(self.data)):
            output.write((self.data[i]^__key[i]).to_bytes())
    
    def separateBytes(self, data):
        self.__data = data
        __evenbytes = []
        __oddbytes = []
        for __byte in range(len(self.__data)):
            if __byte % 2:
                __oddbytes.append(self.__data[__byte])
            else:
                __evenbytes.append(self.__data[__byte])
        return (__evenbytes, __oddbytes)

    def evenfrequency(self, evenbytes):
        self.__evenbytes = evenbytes
        __startsequenc = []
        __evencounters = [[] for _ in range(16)]
        __pluscounters = [[] for _ in range(16)]
        __decicounters = [[] for _ in range(16)]
        
        __strtcounters = [[] for _ in range(16)]
        __finicounters = [[] for _ in range(16)]
        for __byte in range(len(self.__evenbytes)):
            __evencounters[__byte%16].append(self.__evenbytes[__byte])
        for __index in range(len(__evencounters)):
            for __count in range(len(__evencounters[__index])):
                __decicounters[__index].append(__evencounters[__index][__count]&15)
                if __count != len(__evencounters[__index])-1:
                    __param = (__evencounters[__index][__count]+16)%256 == (__evencounters[__index][__count+1])%256
                    __pluscounters[__index].append(int(__param))
                    if __param:
                        __finicounters[__index].append([__count, __decicounters[__index][__count], 2, __evencounters[__index][__count], __evencounters[__index][__count+1]])
        del __decicounters
        
        for __index in range(len(__pluscounters)):
            for __index2 in range(len(__pluscounters[__index])):
                if __pluscounters[__index][__index2] == 1:
                    __strtcounters[__index].append([__index2, ((__evencounters[__index][__index2]&240)-(16*__index2))%256, 2, __evencounters[__index][__index2]&240, __evencounters[__index][__index2+1]&240])
        del __pluscounters, __evencounters
        
        for __index in range(len(__finicounters)):
            for __index2 in reversed(range(1, len(__finicounters[__index]))):
                if __finicounters[__index][__index2][0]-1 == __finicounters[__index][__index2-1][0]:
                    __ranger = reversed(range(1+(__finicounters[__index][__index2-1][2]*-1), 0))
                    for __value in __ranger:
                        __finicounters[__index][__index2-1][4]= __finicounters[__index][__index2][__value]
                        __finicounters[__index][__index2-1][2]= __finicounters[__index][__index2][2]+1
                        del __finicounters[__index][__index2]
        
        __evaluation = [self.evaluate(__strtcounters), self.evaluate(__finicounters)]
        del __strtcounters, __finicounters
        
        for __index in range(len(__evaluation[1])):
            __startsequenc.append(int(__evaluation[1][__index][0][__evaluation[1][__index][1].index(max(__evaluation[1][__index][1]))]))
            __startsequenc[__index]+=int(__evaluation[0][__index][0][__evaluation[0][__index][1].index(max(__evaluation[0][__index][1]))])
        return __startsequenc
        
    def evaluate(self, group):
        self.__group = group
        __returngroup = []
        for __index in range(len(self.__group)):
            __numcount = []
            __numpower = []
            for __index2 in range(len(self.__group[__index])):
                if str(self.__group[__index][__index2][1]) not in __numcount:
                    __numcount.append(str(self.__group[__index][__index2][1]))
                    __numpower.append(2**self.__group[__index][__index2][2])
                else:
                    __ind = __numcount.index(str(self.__group[__index][__index2][1]))
                    __numpower[__ind]+=(2**self.__group[__index][__index2][2])
            __returngroup.append([__numcount, __numpower])
        return __returngroup
    
    def oddcounterold(self, oddbytes):
        self.__oddbytes = oddbytes
        __truefalse = ""
        __pattern = "1010010101001010101001010101001010101001010101001010100101010100101010100101010100101010010101010010101010010101010010101001010101001010101001010101001010100101010100101010100101010100101010100101010010101010010101010010101010010101001010101001010101001010"
        __patterngroups = self.splitPattern(__pattern, 3, len(__pattern))
        __patternoffset = []
        __foundpatterns = []
        
        for __pat in range(len(__patterngroups)):
            __patternoffset.append([(len(__pattern)-__x.start())%len(__pattern) for __x in re.finditer(f'(?=({__patterngroups[__pat]}))', __pattern+__pattern[0:len(__patterngroups[__pat])-1])])
        
        for __byte in range(len(self.__oddbytes)-1):
            if self.__oddbytes[__byte] == self.__oddbytes[__byte+1]:
                __truefalse+="0"
            elif (self.__oddbytes[__byte]+1) == self.__oddbytes[__byte+1]:
                __truefalse+="1"
            else:
                __truefalse+="3"
        __offsets = []
        for __patconfig in __patterngroups[::-1]:
            for __offset in re.finditer(__patconfig, __truefalse):
                __offsetrange = list(range(__offset.start(),__offset.end()))
                if not any(__off in __offsetrange for __off in __offsets):
                    __foundpatterns.append([__offset.start(), __offset.end(), __patconfig, __patterngroups.index(__patconfig)])
                    for __x in range(len(__offsetrange)):
                        __offsets.append(__offsetrange[__x])
        
        __foundpatterns.sort(key=lambda __start: __start[0])
        print(__foundpatterns)
        
        __chains = [[] for _ in range(len(__foundpatterns))]
        
        for __pat in range(len(__foundpatterns)-1):
            print(__patternoffset[__foundpatterns[__pat][3]])
        #for __i in range(len(__foundpatterns)):
        #    print(self.__oddbytes[__foundpatterns[__i][0]:__foundpatterns[__i][1]])
        #print(__truefalse)
        #print(self.__oddbytes)
    
    def splitPattern(self, pattern, minvalue=0, maxvalue=0):
        if not minvalue: minvalue = len(pattern)
        if not maxvalue: maxvalue = minvalue+1
        else: maxvalue+=1
        self.__pattern = pattern
        __patterns = []
        __values = []
        __valuerange = list(range(minvalue,maxvalue))
        for __index in range(len(__valuerange)):
            for __byte in range(len(self.__pattern)):
                __value = self.__pattern[0:__valuerange[__index]]
                if __value not in __values:
                    __values.append(__value)
                self.__pattern+=self.__pattern[0]
                self.__pattern=self.__pattern[1:]
            __values.reverse()
            for __v in __values:
                __patterns.append(__v)
        return __patterns
    
    def generateKey(self, even, length):
        __key = ""
        __pattern = "1010010101001010101001010101001010101001010101001010100101010100101010100101010100101010010101010010101010010101010010101001010101001010101001010101001010100101010100101010100101010100101010100101010010101010010101010010101010010101001010101001010101001010"
        self.__even = even
        self.__length = length
        __b = 1
        for __byte in range(self.__length):
            if __byte % 2:
                __key+=__b.to_bytes().hex()
                __b+=int(__pattern[(__byte//2)%len(__pattern)])
                __b=__b%len(__pattern)
            else:
                __key+=((self.__even[(__byte//2)&15]+((__byte//32)*16)%256)%256).to_bytes().hex()
        return bytearray.fromhex(__key)
        
        
if __name__ == "__main__":
  try:
    file = sys.argv[1]
  except IndexError:
    print >> sys.stderr, "The file is not here"
    sys.exit(1)
  output = file+"_output.dat"
  reader = IIDX6Decrypt(bytearray(open(file, "rb").read()), open(output, "wb"))