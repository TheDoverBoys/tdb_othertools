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
        __headersizes = []
        __chunkcontents = []
        __previous_increment = 0
        __increment = 0
        __chunksize = 8
        __chunks = []
        while len(__chunks) < 12:
            __headersize = int.from_bytes(bindata[0+__increment:4+__increment], "little")
            if len(__headersizes) < 2:
                __chunksize = 8
            else:
                __chunksize = 42
            __headersizes.append(__headersize)
            __previous_increment = __increment
            __increment += (__headersize*__chunksize)+4
            __chunkcontents = bindata[4+__previous_increment:__increment]
            __chunks.append(__chunkcontents)
        return __chunks
    
    def parseTempo(self, chunk):
        self.__chunk = chunk
        __tick_rate = 150
        __beats = []
        __seconds = []
        for __index in range(len(self.__chunk)//8):
            __beat = int.from_bytes(self.__chunk[__index*8:4+(__index*8)], byteorder='little', signed=True)/1024
            __second = int.from_bytes(self.__chunk[4+(__index*8):8+(__index*8)], byteorder='little', signed=True)
            __beats.append(__beat)
            __seconds.append(__second/__tick_rate)


        __bpms = []
        __stops = []
        __warps = []

        try:
            __start_position = __beats.index(0)
        except:
            __start_position = [None]
        else:
            __start_position = __beats.index(0)
        
        if __start_position == [None]:
            __beat_interval = __beats[1]-__beats[0]
            __seconds_interval = __seconds[1]-__seconds[0]
            __incrim_bpm = (__beat_interval/__seconds_interval)*60
            __incriminator = __beats[0]*(-1)
            __beats[0] += __incriminator
            __seconds[0] -= (60/__incrim_bpm)*(__incriminator*(-1))
            __offset = __seconds[0]*(-1)
        else:
            __offset = __seconds[__start_position]*(-1)

        for i in range(len(__beats)-1):
            __beat_interval = __beats[i+1]-__beats[i]
            __seconds_interval = __seconds[i+1]-__seconds[i]
            if __beat_interval == 0:
                __stops.append([__beats[i], __seconds_interval])
            elif __seconds_interval == 0:
                __warps.append([__beats[i], __beat_interval])
            elif __beat_interval == 0 and __seconds_interval == 0:
                continue
            else:
                __bpm = [__beats[i], (__beat_interval/__seconds_interval)*60]
                __bpms.append(__bpm)

        return (__bpms, __stops, __warps, __offset)

    def parseEvents(self, chunk):
        subevent_lookup = {
            0x00: "last_last_finish",
            0x01: "first_beat",
            0x02: "here_we_go",
            0x03: "first_step", 
            0x04: "last_finish",
            0x05: "screen_transition"
        }
        self.__chunk = chunk
        __events = []
        __timesignatures = []
        for __index in range(len(self.__chunk)//8):
            __beat = int.from_bytes(self.__chunk[__index*8:4+(__index*8)], byteorder='little', signed=True)/1024
            __event = self.__chunk[4+(__index*8)]
            if self.__chunk[5+(__index*8)]:
                if __event == 0x01: __timesignatures.append([__beat, self.__chunk[5+(__index*8)]])
            else: __events.append([__beat, subevent_lookup.get(__event)])
        return (__events, __timesignatures)

    def parseNotes(self, chunk):
        self.__chunk = chunk
        __note_lookup = {
            0: "Left",
            1: "Down",
            2: "Up",
            3: "Right",
            4: "Left 2P",
            5: "Down 2P",
            6: "Up 2P",
            7: "Right 2P"
        }

        __beats = []
        __notes = []
        __freezestarts = []
        __freezeends = []
        for index in range(len(self.__chunk)//42):
            __beat = int.from_bytes(self.__chunk[34+(index*42):38+(index*42)], byteorder='little', signed=True)/1024
            __note = []
            __note_value = self.__chunk[index*42]
            __holdmarker = self.__chunk[1+(index*42)]
            __notea = []
            __prioritya = []
            __noteb = []
            __priorityb = []
            for note_side_index in range(2):
                for arrow_index in range(4):
                    if (__note_value >> (note_side_index*4)+arrow_index) & 1:
                        if __holdmarker == 1:
                            if not __notea:
                                __notea = ((note_side_index*4)+arrow_index)+1
                                __prioritya = int.from_bytes(self.__chunk[2+(((note_side_index*4)+arrow_index)*4)+(index*42):6+(((note_side_index*4)+arrow_index)*4)+(index*42)], 'little')
                            else:
                                __noteb = ((note_side_index*4)+arrow_index)+1
                                __priorityb = int.from_bytes(self.__chunk[2+(((note_side_index*4)+arrow_index)*4)+(index*42):6+(((note_side_index*4)+arrow_index)*4)+(index*42)], 'little')
                        else:
                            __note.append((note_side_index*4)+arrow_index)
                        continue
            if __notea and not __note:
                if __noteb:
                    if __prioritya < __priorityb:
                        __note.append(__notea-1)
                        __note.append(__noteb-1)
                    else:
                        __note.append(__noteb-1)
                        __note.append(__notea-1)
                else:
                    __note.append(__notea-1)
            if (__note_value & 255) == 0:
                __note.append(-1)
                __freezeends.append(__beat)
            else:
                __priority_value = []
                if __holdmarker == 1:
                    for note_index in range(len(__note)):
                        __priority_check = int.from_bytes(self.__chunk[2+(index*42)+(__note[note_index]*4):6+(index*42)+(__note[note_index]*4)], byteorder='little', signed=True)
                        if __priority_check == -1: __priority_check = []
                        __priority_value.append(__priority_check)
                    if len(__priority_value) > 1:
                        if __priority_value[0]:
                            if __priority_value[1]:
                                if __priority_value[0] > __priority_value[1]:
                                    __freezestarts.append([__beat, __note[1]])
                                    __freezestarts.append([__beat, __note[0]])
                                elif __priority_value[0] < __priority_value[1]:
                                    __freezestarts.append([__beat, __note[0]])
                                    __freezestarts.append([__beat, __note[1]])
                                else:
                                    break
                            else:
                                __freezestarts.append([__beat, __note[0]])
                        elif __priority_value[1]:
                            __freezestarts.append([__beat, __note[1]])
                    else:
                        __freezestarts.append([__beat, __note[0]])
                else:
                        ...
            for note_index in range(len(__note)):
                __beats.append(__beat)
                __notes.append(__note[note_index])

        return __beats, __notes, __freezestarts, __freezeends

    def writeSm(self, output, tempo, events, charts):
        __chart_style = {
            0: "dance-single",
            1: "dance-double"
        }
        __difficulty_level = {
            0: "Beginner",
            1: "Easy",
            2: "Medium",
            3: "Hard",
            4: "Challenge"
        }
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
            if charts[chart][0]:
                __chartString = "\n#NOTES:"+__chart_style.get(chart//5)+"::"+__difficulty_level.get(self.reduceByFive(chart))+":1::\n"
                __lastbeat = math.ceil(charts[chart][0][len(charts[chart][0])-1])
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
                    for beatindex in range(len(charts[chart][0])):
                        if not self.verifyingroup(__beatAppend,[charts[chart][0][beatindex], charts[chart][1][beatindex], 4, beatindex]):
                            if (beatcount//4)*4 <= charts[chart][0][beatindex] < math.ceil(beatcount/4)*4:
                                __beatAppend.append([charts[chart][0][beatindex], charts[chart][1][beatindex], 4, beatindex])
                for freezearrowindex in range(len(charts[chart][2])):
                    for measureindex in range(len(__measures)):
                        for beatindex in range(len(__measures[measureindex])):
                            if (charts[chart][2][freezearrowindex][0] == __measures[measureindex][beatindex][0]) and (charts[chart][2][freezearrowindex][1] == __measures[measureindex][beatindex][1]):
                                __measures[measureindex][beatindex].append(True)

                output.write(__chartString)
                __measureAppend = []
                
                for measureindex in range(len(__measures)):
                    self.reduction(__measures)
                    self.recursionApproximate(__measures[measureindex])
                    if not __measures[measureindex]:
                        if __chart_style.get(chart//5) == "dance-double":
                            __measure_write = [[0,0,0,0,0,0,0,0]]
                        else:
                            __measure_write = [[0,0,0,0]]
                        __measureAppend.append(__measure_write*4)
                    else:
                        __measure_divide = []
                        __measure_write = []
                        for beatindex in range(len(__measures[measureindex])):
                            __measure_divide.append(__measures[measureindex][beatindex][2])
                        __measure_max_divide = int(max(__measure_divide))
                        for i in range(__measure_max_divide):
                            if __chart_style.get(chart//5) == "dance-double":
                                __measure_write.append([0,0,0,0,0,0,0,0])
                            else:
                                __measure_write.append([0,0,0,0])
                        for beatindex in range(len(__measures[measureindex])):
                            __measures[measureindex][beatindex][0] *= __measure_max_divide/__measures[measureindex][beatindex][2]
                            __measures[measureindex][beatindex][2] = __measure_max_divide
                        __measureAppend.append(__measure_write)
                if __chart_style.get(chart//5) == "dance-double":
                    __lastbeat = [None]*8
                else:
                    __lastbeat = [None]*4
                #print(__measureAppend)
                
                __freezepool = []
                for measureindex in range(len(__measureAppend)):
                    if __measures[measureindex]:
                        for barget in range(len(__measures[measureindex])):
                            for barget2 in range(len(__measureAppend[measureindex])):
                                if barget2 == int(__measures[measureindex][barget][0]):
                                    if len(__measures[measureindex][barget]) == 5:
                                        __freezepool.append([__measures[measureindex][barget][0], __measures[measureindex][barget][1]])
                                        __measureAppend[measureindex][int(__measures[measureindex][barget][0])][__measures[measureindex][barget][1]] = 2
                                    else:
                                        __lastbeat[__measures[measureindex][barget][1]] = (measureindex, int(__measures[measureindex][barget][0]))
                                        if __measures[measureindex][barget][1] == -1:
                                            __measureAppend[measureindex][int(__measures[measureindex][barget][0])][__freezepool[0][1]] = 3
                                            del __freezepool[0]
                                        else:
                                            __measureAppend[measureindex][int(__measures[measureindex][barget][0])][__measures[measureindex][barget][1]] = 1
                                
                for measureindex in range(len(__measureAppend)):
                    for barget in range(len(__measureAppend[measureindex])):
                        __measureString = ""
                        for arrowget in range(len(__measureAppend[measureindex][barget])):
                            __measureString += str(__measureAppend[measureindex][barget][arrowget])
                        output.write(__measureString)
                        output.write("\n")
                    if measureindex != len(__measureAppend)-1:
                        output.write(",\n")
                output.write(";\n\n")
                
    def reduceByFive(self, number):
        self.__number = number
        if self.__number >= 5:
            self.__number -= 5
        return self.__number
    
    def verifyingroup(self, group, number):
        for i in range(len(group)):
            if group[i] == number: return True
        return False
    
    def reduction(self, group):
        self.__group = group
        for index in range(len(self.__group)):
            if self.__group[index]:
                for index2 in range(len(self.__group[index])):
                    self.__division = self.__group[index][index2][2]
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
                self.__lastIncrease = self.__group[index][2]
                self.__denominator = Fraction(self.__beatFractioned).denominator
                self.__group[index][0] *= (self.__denominator*4)/self.__lastIncrease
                self.__group[index][2] *= (self.__denominator*4)/self.__lastIncrease
                if 192 % self.__group[index][2] != 0:
                    self.__group[index][0] = round(self.__group[index][0]*(192/self.__group[index][2]))
                    self.__group[index][2] = 192
        return self.__group

if __name__ == "__main__":
    file = sys.argv[1]
    output = file+".sm"
    reader = SsfourReader(bytearray(open(file, "rb").read()), open(output, "w"))