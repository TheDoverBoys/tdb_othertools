import sys, math
from fractions import Fraction

sys.setrecursionlimit(1000)

class SsfourReader:
    def __init__(self, data, output):
        self.data = data
        chunks = self.getHeaders(self.data)
        tempo = self.parseTempo(chunks[0])
        events = self.parseEvents(chunks[1])
        charts = []
        for i in range(2, len(chunks)):
            chart = self.parseNotes(chunks[i])
            charts.append(chart)
        self.writeSm(output, tempo, events, charts)
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
    
    def writeSm(self, output, tempo, events, charts):
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
        
class MergeCouples:
    def __init__(self, file, output):
        __unconcatenated = open("output"+output, "w")
        __charts = []
        self.sectionFinder(str(file), __unconcatenated)
        
    def sectionFinder(self, file, outputfile):
        self.file = file.splitlines( )
        __ranges = []
        __ends = []
        __leftranges = []
        __rightranges = []
        #find sections
        for line_number, line in enumerate(self.file, start=1):
            self.findSection(__ranges, 'dance-', line, line_number)
            if line == ';':
                __ends.append(line_number)
        if len(__ranges) == len(__ends):
            for sections in range(len(__ranges)):
                __ranges[sections] = [__ranges[sections], __ends[sections]]
        for line_number, line in enumerate(self.file, start=1):
            for start_length in range(len(__ranges)):
                if line == self.file[__ranges[start_length][0]-1]:
                    self.findSection(__leftranges, 'dance-couple', line, [__ranges[start_length][0], __ranges[start_length][1]])
                    self.findSection(__rightranges, 'dance-routine', line, [__ranges[start_length][0], __ranges[start_length][1]])
            if not __leftranges:
                outputfile.write(str(line)+"\n")
        if not __leftranges:
            return

        __singleranges = []
        for rangeindex in range(len(__ranges)):
            if not __ranges[rangeindex] in __leftranges and not __ranges[rangeindex] in __rightranges:
                __singleranges.append(__ranges[rangeindex])
        for singlerange in range(len(__singleranges)):
            if __singleranges[singlerange][0] > min(__leftranges[0][0], __rightranges[0][0]):
                for chartrange in range(__singleranges[singlerange][0]-__singleranges[singlerange][0], __singleranges[singlerange][1]-__singleranges[singlerange][0]+1):
                    outputfile.write(self.file[__singleranges[singlerange][0]-1+chartrange]+"\n")
        #separate sections
        __leftsections = []
        __rightsections = []
        __leftmeasures = []
        __rightmeasures = []
        if len(__leftranges) == len(__rightranges):
            for sectionindex in range(len(__leftranges)):
                __leftsections.append(self.file[__leftranges[sectionindex][0]:__leftranges[sectionindex][1]-1])
                __rightsections.append(self.file[__rightranges[sectionindex][0]:__rightranges[sectionindex][1]-1])
                __leftmeasures.append(self.measureDivider(__leftsections[sectionindex], ","))
                __rightmeasures.append(self.measureDivider(__rightsections[sectionindex], ","))
        
        #unite everything
        __newmeasures = []
        __newcharts = []
        if len(__leftmeasures) == len(__rightmeasures):
            for chartindex in range(len(__leftmeasures)):
                __newsections = []
                if len(__leftmeasures[chartindex]) == len(__rightmeasures[chartindex]):
                    for sectionindex in range(len(__leftmeasures[chartindex])):
                        __newbeats = []
                        __sectionlcm = math.lcm(len(__leftmeasures[chartindex][sectionindex]), len(__rightmeasures[chartindex][sectionindex]))
                        self.correctMeasure(__sectionlcm, __leftmeasures[chartindex][sectionindex])
                        self.correctMeasure(__sectionlcm, __rightmeasures[chartindex][sectionindex])
                        for beatindex in range(__sectionlcm):
                            __leftappend = __leftmeasures[chartindex][sectionindex][beatindex][:4]
                            __rightappend = __rightmeasures[chartindex][sectionindex][beatindex][4:]
                            __newbeats.append(__leftappend+__rightappend)
                        __newsections.append(__newbeats)
                __newcharts.append(__newsections)
            __newmeasures.append(__newcharts)
        
        #paste everything
        
        for chartindex in range(len(__newmeasures)):
            for sectionindex in range(len(__newmeasures[chartindex])):
                outputfile.write(str(self.file[__leftranges[sectionindex][0]-1])+"\n")
                for beatindex in range(len(__newmeasures[chartindex][sectionindex])):
                    __unconcatenated_beats = []
                    for arrowindex in range(len(__newmeasures[chartindex][sectionindex][beatindex])):
                        __unconcatenated_beats.append(__newmeasures[chartindex][sectionindex][beatindex][arrowindex])
                    for uncbeatindex in range(len(__unconcatenated_beats)):
                        for uncarrowindex in range(len(__unconcatenated_beats[uncbeatindex])):
                            outputfile.write(str(__unconcatenated_beats[uncbeatindex][uncarrowindex]))
                        outputfile.write("\n")
                    outputfile.write(",\n")
                outputfile.write(";\n")
        return
                    
    def findSection(self, group, string, line, line_number):
        if string in line:
            group.append(line_number)
        return group
    
    def recursiveSubtractor(self, group, limiter):
        self.group = group
        self.limiter = limiter
        for length in range(len(self.group)):
            if self.group[length] < self.limiter:
                self.group.pop(0)
                self.recursiveSubtractor(self.group, self.limiter)
            return self.group
        return
    
    def measureDivider(self, group, dividerstring):
        __beats = []
        __measures = []
        self.__group = group
        self.__dividerstring = dividerstring
        for measureindex in range(len(self.__group)):
            for beatindex in range(len(self.__group[measureindex])):
                if not self.__group[measureindex][beatindex] == self.__dividerstring:
                    if not beatindex % 8:
                        __beats.append([self.__group[measureindex][beatindex],self.__group[measureindex][beatindex+1],self.__group[measureindex][beatindex+2],self.__group[measureindex][beatindex+3],self.__group[measureindex][beatindex+4],self.__group[measureindex][beatindex+5],self.__group[measureindex][beatindex+6],self.__group[measureindex][beatindex+7]])
                else:
                    __measures.append(__beats)
                    __beats = []
        return __measures

    def correctMeasure(self, lcm, measure):
        self.__lcm = lcm
        self.__measure = measure
        self.__length = len(self.__measure)
        if self.__lcm > self.__length:
            self.__modulo = ((self.__lcm-self.__length)//self.__length)+1
            for lcmrange in range(self.__length-1, -1, -1):
                for modulorange in range(1, self.__modulo+1):
                    if modulorange % self.__modulo:
                        self.__measure.insert(lcmrange+1, [0,0,0,0,0,0,0,0])
        return

if __name__ == "__main__":
    file = sys.argv[1]
    output = file+".sm"
    reader = SsfourReader(bytearray(open(file, "rb").read()), open(output, "w"))
    merger = MergeCouples(open(output, "r").read(), output)