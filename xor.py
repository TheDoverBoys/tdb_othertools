import sys, os

def everything(file, key):
  fileData = file.read()
  keyData = key.read()
  fileDir = './extracted/'
  if not os.path.isdir(fileDir):
    os.mkdir(fileDir)
  fileName = open(os.path.join(fileDir,os.path.basename(sys.argv[1])),"wb")
  for i in range(len(fileData)):
    fileName.write((fileData[i]^keyData[i%len(keyData)]).to_bytes())
  fileName.close()

if __name__ == "__main__":
  try:
    referenceFile = open(sys.argv[1],"rb")
    keyFile = open('key.dat',"rb")
  except IndexError:
    print("The files are not here")
    exit()
  everything(referenceFile, keyFile)