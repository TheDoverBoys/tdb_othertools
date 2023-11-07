#Author: TheDoverBoys
from inc_noesis import *

def registerNoesisTypes():
    handle = noesis.register("Ssamba Festival .gsb textures", ".gsb")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadRGBA(handle, noepyLoadRGBA)
    return 1

def noepyCheckType(data):
    bs = NoeBitStream(data)
    return 1

def noepyLoadRGBA(data, texList):
    bs = NoeBitStream(data)
    bs.setEndian(NOE_LITTLEENDIAN)
    numberoffiles = bs.readInt()
    for i in range(numberoffiles):
        width = bs.readInt()
        height = bs.readInt()
        unk1 = bs.readInt()
        unk2 = bs.readInt()
        unk3 = bs.readInt()
        zero = bs.readInt()
        unkNum = bs.readInt()
        pixel = bs.readBytes(width*height*2)
        textureData = rapi.imageDecodeRaw(pixel,width,height,"a0b5g6r5")
        texList.append(NoeTexture(rapi.getInputName(), width, height, textureData, noesis.NOESISTEX_RGBA32))   
    return 1