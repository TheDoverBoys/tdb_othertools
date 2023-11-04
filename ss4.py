import sys, math
from fractions import Fraction

sys.setrecursionlimit(1000)

class SsfourReader:
    def __init__(self, data):
        self.data = data
        chunks = self.getHeaders(self.data)
        tempo = self.parseTempo(chunks[0])
        events = self.parseEvents(chunks[1])
        charts = []
        for i in range(2, len(chunks)):
            chart = self.parseNotes(chunks[i])
            charts.append(chart)
        self.writeSm(tempo, events, charts)
        print("Loaded successfully!")

    def getHeaders(self, bindata):
        __headers = []
        __increments = []
        __increment = 0
        while bindata[0+__increment] or bindata[1+__increment] or bindata[2+__increment] or bindata[3+__increment]:
            __increments.append(__increment)
            __header = int.from_bytes(bindata[0+__increment:4+__increment], "little")
            __increment += __header
            __headers.append(__header)
        __chunks = []
        for n in range(len(__increments)):
            __chunk = bindata[__increments[n]:__increments[n]+__headers[n]]
            __chunks.append(__chunk)
        return __chunks

        
    def parseTempo(self, chunk):
        #__length = int.from_bytes(chunk[0:4], "little")
        __beat_divider = int.from_bytes(chunk[4:6], "little")
        __tick_rate = int.from_bytes(chunk[6:8], "little")
        __tempo_event_number = int.from_bytes(chunk[8:12], "little")
        __beats = []
        __seconds = []
        for i in range(__tempo_event_number):
            __beat = (int.from_bytes(chunk[13+(i*4):16+(i*4)], "little") + chunk[12+(i*4)]/256)/4
            __second = int.from_bytes(chunk[20+(i*4)+((__tempo_event_number-2)*4):24+(i*4)+((__tempo_event_number-2)*4)], "little")
            __beats.append(__beat)
            __seconds.append(__second/(__tick_rate/__beat_divider))

        __bpms = []
        __stops = []
        __warps = []
        __offset = __seconds[0]*(-1)
        for i in range(len(__beats)-1):
            __beat_interval = __beats[i+1]-__beats[i]
            __seconds_interval = __seconds[i+1]-__seconds[i]
            if __beat_interval == 0:
                __stops.append([__beats[i], __seconds_interval])
            elif __seconds_interval == 0:
                __warps.append([__beats[i], __beat_interval])
            elif __beat_interval == 0 and __seconds_interval == 0:
                pass
            else:
                __bpm = [__beats[i], (__beat_interval/__seconds_interval)*60]
                __bpms.append(__bpm)
        return (__bpms, __stops, __warps, __offset)
    
    def parseEvents(self, chunk):
        subevent_lookup = {
            0x01: "first_beat",
            0x02: "here_we_go",
            0x03: "chart_end", 
            0x04: "last_finish",
            0x05: "scroll_edit"
        }
        __events = []
        __timesignatures = []
        #__length = int.from_bytes(chunk[0:4], "little")
        __event_number = int.from_bytes(chunk[8:12], "little")
        for i in range(__event_number):
            __beat = (int.from_bytes(chunk[13+(i*4):16+(i*4)], "little") + chunk[12+(i*4)]/256)/4
            __event = chunk[20+(i*2)+((__event_number-2)*4)]
            if __event == 0x02: __events.append([__beat, subevent_lookup.get(chunk[21+(i*2)+((__event_number-2)*4)])])
            elif __event == 0x01: __timesignatures.append([__beat, chunk[21+(i*2)+((__event_number-2)*4)]])
        return (__events, __timesignatures)
            
    def parseNotes(self, chunk):
        __chart_type = {
            0x14: "dance-single",
            0x24: "dance-couple",           # Couple 1P
            0x34: "dance-routine"           # Couple 2P
        }
        '''
        Unsupported Types
        0x1A: "choreo-single",
        0x2A: "choreo-couple",              # Couple 1P
        0x3A: "choreo-battle",              # Couple 2P
        0x4A: "wiibb-single"                # Wii Balance Board
        '''
        __difficulty_type = {
            0x01: "Easy",
            0x02: "Medium",
            0x03: "Hard",
            0x04: "Beginner",
            0x06: "Challenge"
        }
        __note_lookup = {
            0x00: "Left",
            0x01: "Down",
            0x02: "Up",
            0x03: "Right"
        }
        #__length = int.from_bytes(chunk[0:4], "little")
        __type = int.from_bytes(chunk[4:6], "little")
        if __type == 0x10:
            __chart = chunk[6]
            if __chart_type.get(__chart):
                __difficulty = chunk[7]
                print(__chart_type.get(__chart), __difficulty_type.get(__difficulty))
                __note_number = int.from_bytes(chunk[8:12], "little")
                __modulo = 0
                if __note_number % 4:
                    __modulo = 4-(__note_number % 4)
                
                __beats = []
                __notes = []
                __freezeends = []
                for i in range(__note_number):
                    if __note_lookup.get(chunk[12+i+(__note_number*4)]):
                        __note = chunk[12+i+(__note_number*4)]
                        __beat = (int.from_bytes(chunk[13+(i*4):16+(i*4)], "little") + chunk[12+(i*4)]/256)/4
                        __freezeend = chunk[14+(i*4)+(__note_number*4)+(__note_number+__modulo)]
                        __beats.append(__beat)
                        __notes.append(__note)
                        __freezeends.append(__freezeend)
                    else:
                        print("Unrecognized note value! "+str(chunk[12+i+(__note_number*4)]))
                return __chart_type.get(__chart), __difficulty_type.get(__difficulty), __beats, __notes, __freezeends, 4
        return
    
    def writeSm(self, tempo, events, charts):
        output = open(file+".sm", "w")
        output.write("#TITLE:Untitled;\n#ARTIST:;\n#MUSIC:song.ogg;\n")
        __tempoString = "#OFFSET:"+str(tempo[3])+";\n#BPMS:"
        for t_event in range(len(tempo)-2): #-1):
            if t_event == 1: __tempoString += "#STOPS:"
            elif t_event == 2: __tempoString += "#WARPS:"
            for index in range(len(tempo[t_event])):
                __tempoString += str(tempo[t_event][index][0])+"="+str(tempo[t_event][index][1])
                if index < len(tempo[t_event])-1: __tempoString += ","
            __tempoString += ";\n"
        output.write(__tempoString)
        
        for chart in range(len(charts)):
            if charts[chart]:
                __chartString = "\n#NOTES:"+charts[chart][0]+"::"+charts[chart][1]+":1::\n"
                __lastbeat = math.ceil(charts[chart][2][len(charts[chart][2])-1])
                __lastmeasure = math.ceil(__lastbeat/4)
                for event in range(len(events[0])):
                    if events[0][event][1] == 'last_finish':
                        __lastbeat = events[0][event][0]
                        __lastmeasure = math.ceil(__lastbeat/4)
                __measures = []
                __beatAppend = []
                for beatcount in range(1+__lastmeasure*4):
                    if beatcount % 4 == 0 and beatcount != 0:
                        __measures.append(__beatAppend)
                        __beatAppend = []
                    for beatindex in range(len(charts[chart][2])):
                        if (beatcount//4)*4 <= charts[chart][2][beatindex] < math.ceil(beatcount/4)*4:
                            if not __beatAppend or not self.verifyingroup(__beatAppend,[charts[chart][2][beatindex], charts[chart][3][beatindex], charts[chart][4][beatindex], 4]):
                                __beatAppend.append([charts[chart][2][beatindex], charts[chart][3][beatindex], charts[chart][4][beatindex], 4])
                
                output.write(__chartString)
                __measureAppend = []
                for measureindex in range(len(__measures)):
                    self.reduction(__measures)
                    self.recursionApproximate(__measures[measureindex])
                    if not __measures[measureindex]:
                        __measure_write = [[0,0,0,0]]
                        __measureAppend.append(__measure_write*4)
                    else:
                        __measure_divide = []
                        __measure_write = []
                        for beatindex in range(len(__measures[measureindex])):
                            __measure_divide.append(__measures[measureindex][beatindex][3])
                        __measure_max_divide = int(max(__measure_divide))
                        for i in range(__measure_max_divide):
                            __measure_write.append([0,0,0,0])
                        for beatindex in range(len(__measures[measureindex])):
                            __measures[measureindex][beatindex][0] *= __measure_max_divide/__measures[measureindex][beatindex][3]
                            __measures[measureindex][beatindex][3] = __measure_max_divide
                        __measureAppend.append(__measure_write)
                __lastbeat = [None]*4
                for measureindex in range(len(__measureAppend)):
                    if __measures[measureindex]:
                        for barget in range(len(__measures[measureindex])):
                            for barget2 in range(len(__measureAppend[measureindex])):
                                if barget2 == int(__measures[measureindex][barget][0]):
                                    if __measures[measureindex][barget][2] == 1:
                                        __measureAppend[__lastbeat[__measures[measureindex][barget][1]][0]][__lastbeat[__measures[measureindex][barget][1]][1]][__measures[measureindex][barget][1]] = 2
                                        __measureAppend[measureindex][int(__measures[measureindex][barget][0])][__measures[measureindex][barget][1]] = 3
                                    else:
                                        __lastbeat[__measures[measureindex][barget][1]] = (measureindex, int(__measures[measureindex][barget][0]))
                                        __measureAppend[measureindex][int(__measures[measureindex][barget][0])][__measures[measureindex][barget][1]] = 1
                for measureindex in range(len(__measureAppend)):
                    for barget in range(len(__measureAppend[measureindex])):
                        __measureString = ""
                        for arrowget in range(len(__measureAppend[measureindex][barget])):
                            __measureString += str(__measureAppend[measureindex][barget][arrowget])
                        if charts[chart][0] == "dance-routine":
                            output.write("0000")
                        output.write(__measureString)
                        if charts[chart][0] == "dance-couple":
                            output.write("0000")
                        output.write("\n")
                    if measureindex != len(__measureAppend)-1:
                        output.write(",\n")
            output.write(";\n\n")
    
    def verifyingroup(self, group, number):
        for i in range(len(group)):
            if group[i] == number: return True
        return False
        
    def reduction(self, group):
        self.__group = group
        for index in range(len(self.__group)):
            if self.__group[index]:
                for index2 in range(len(self.__group[index])):
                    self.__division = self.__group[index][index2][3]
                    __minimumvalue = (self.__group[index][index2][0]//self.__division)*self.__division
                    self.__group[index][index2][0] -= __minimumvalue
        return self.__group
        
    def recursionApproximate(self, group):
        self.__group = group
        if self.__group:
            for index in range(len(self.__group)):
                if not (self.__group[index][0] % 1) == 0:
                    self.recursionFailure(self.__group)
                    self.recursionApproximate(self.__group)
        return self.__group
        
    def recursionFailure(self, group):
        self.__group = group
        if self.__group:
            for index in range(len(self.__group)):
                self.__beatFractioned = self.__group[index][0]
                self.__lastIncrease = self.__group[index][3]
                self.__denominator = Fraction(self.__beatFractioned).denominator
                self.__group[index][0] *= (self.__denominator*4)/self.__lastIncrease
                self.__group[index][3] *= (self.__denominator*4)/self.__lastIncrease
                if 192 % self.__group[index][3] != 0:
                    self.__group[index][0] = round(self.__group[index][0]*(192/self.__group[index][3]))
                    self.__group[index][3] = 192
        return self.__group
        
if __name__ == "__main__":
    file = sys.argv[1]
    #file = "ss4/MU_DDR_012.ss4"
    reader = SsfourReader(bytearray(open(file, "rb").read()))