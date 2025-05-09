import os
import sys

filecount = 0
filestodelete = []
currentfirstlevelfile = 0


def LoadFS(file,arr,offset,parent,recursion):
    global filecount
    global filestodelete
    global currentfirstlevelfile
    initfilecount = filecount
    file.seek(offset)
    magic1 = file.read(1).decode("utf-8");
    magic2 = file.read(1).decode("utf-8");     
    numofoffsets = int.from_bytes(file.read(2),"little")
    if(filecount < 98):
        print("number of offsets in thing")
        print(numofoffsets)
        print("absolute offset")
        print(offset)

    offsets = [None]*(numofoffsets+1)
    #allfound = False
        
        
    for number in range(numofoffsets + 1):
        offsets[number] = file.read(4)
    
    for number in range(numofoffsets):    
        #magic /folder
        arr.append([])
        
        #get parent path[0]
        arr[filecount].append(parent.copy())
        #print("appending magic")
        
        #magic[0] current directory
        arr[filecount][0].append(magic1+magic2+str(currentfirstlevelfile))
        #print("arr"+"["+str(filecount)+"]["+"0"+"]")
        #print(arr[filecount][0])
        
        #file number[1]
        arr[filecount].append(number)
        
        #where to start reading[2]
        if(filecount < 98):
            print("------------------")
            print("byte offset")
            print(offsets[number])
            print("index")
            print(number)
            print("index to be read")
            print(int.from_bytes(offsets[number],"little")+offset)
            print("path")
            print(arr[filecount][0])
            print("------------------")

        arr[filecount].append(int.from_bytes(offsets[number],"little")+offset)
        #if(filecount < 98):
            #print(filecount)
            #print(number)
            #print(arr[filecount][2])
        
        #how long to read file for[3]
        arr[filecount].append(int.from_bytes(offsets[number + 1],"little") - int.from_bytes(offsets[number],"little"))
        
        #print("filecount:")
        filecount = filecount + 1
    
    print(arr[0][2])
    
    
    
     
    #if we find subfolders
    offset = recursion > 1
    offset2 = 0
    if offset:
        offset2 = 1

        
    for number in range(numofoffsets):
        print("offset recursion > 1:")
        print("number in offset list")
        print(initfilecount+number)
        print("looking at offset")
        print(arr[initfilecount+number][2])
        print("offset length")
        print(arr[initfilecount+number][3])
        file.seek(arr[initfilecount+number][2])
        testfile1 = int.from_bytes(file.read(1),"little");
        testfile2 = int.from_bytes(file.read(1),"little");  
        testnumofoffsets = int.from_bytes(file.read(2),"little")
        currentfirstlevelfile = number
        print("currentfirstlevelfile")
        print(currentfirstlevelfile)
        if filecount < 98:
            print("testfilenumbers")
            print(testfile1)
            print(testfile2)
            #check if it's inbetween range and if the offsets actually have any length. also if it has a valid offset length(it can't be more than 0x1C because it only takes up so much space)
        if((testfile1 < 65 or testfile1 > 90) or (testfile2 < 65 or testfile2 > 90) or (arr[initfilecount+number][3] == 0) or (testnumofoffsets > 31)):
            print("subfolder not found")
            print()
            print()
            recursion = recursion + 1
        else:                    
            print("subfolder found")
            print()
            print()
            
            recursion = recursion + 1
            #marking for deletion insead of actually deleting rn
            filestodelete.append(initfilecount+number)
            LoadFS(file,arr,arr[initfilecount+number][2],arr[initfilecount+number][0],recursion)  
            #if we find a subfolder, we need to remove the original "file" we found it in
            

            #filecount = filecount - 1
                
            print("file being deleted")
            print(arr[initfilecount+number][0])
            print("exiting recursion for: ")
            print(number)
            print(arr[initfilecount+number][0])
            print()
            print()
        
            
        #allfound = (count >= (numoffsets - 1))
            
    
def MakeDirs(MasterList,file): 
    count = 0
    for x in MasterList:
            directory_name = ""
            count2 = 0
            for y in MasterList[count][0]:
                directory_name = directory_name+(str(MasterList[count][0][count2])+"/")
                count2 = count2 + 1
                
            try:
                os.makedirs(directory_name)
                print(f"Directory '{directory_name}' created successfully.")
            except FileExistsError:
                print(f"Directory '{directory_name}' already exists.")
            except PermissionError:
                print(f"Permission denied: Unable to create '{directory_name}'.")
            except Exception as e:
                print(f"An error occurre: {e}"+"...")
                
            filetype = checkFileType(MasterList[count][2],file).rstrip('\x00')
            print(filetype)
            filename = (("("+str(MasterList[count][1])+")"+filetype)).replace('\x00','')
            print(filename)
            print(directory_name)
            file.seek(MasterList[count][2])
            filedata = file.read(MasterList[count][3])
            with open(directory_name+filename, "wb") as file1:
                file1.write(filedata)
            count = count + 1
    
def findFileNameGFModel(file):
    fileType = file.read(4)
    filename = ""
    if(fileType == b'\x17\x21\x12\x15'):
        sectionscount = file.read(12)
        modelgfsection = file.read(16)
        for x in range(4):
            numofhashes = int.from_bytes(file.read(4),"little");
            for x2 in range(numofhashes):
                #hash
                file.read(4)
                #name
                string = file.read(64).decode("utf-8").strip('\x00')
                
                if (x == 2 and x2 == 0):
                    print("chosen")
                    filename = string    
        
        file.seek(file.tell()+96)
        unknowndatalength = int.from_bytes(file.read(4),"little")
        unknowndataoffset = int.from_bytes(file.read(4),"little")
        file.seek(file.tell()+4)
        file.seek(file.tell()+unknowndataoffset+4)
        
        bonescount = int.from_bytes(file.read(4),"little")
        file.seek(file.tell()+12)
        
        #get first bone name for more "accurate model name"
        if bonescount > 0:
            stringlength = int.from_bytes(file.read(1),"little")
            string2 = file.read(stringlength).decode("utf-8").strip('\x00')
            filename = string2
            
            
    return filename
            
def checkFileType(offset,file):
    OverrideFileName = False
    #skip first 16 bytes to check for gfsection
    magic = "bin"
    file.seek(offset)
    print(file.tell())
    bytedata0 = file.read(8)
    file.seek(offset+16)
    bytedata = file.read(8)
    print(bytedata)
    
    #is it a shader?
    if(bytedata == b'\x73\x68\x61\x64\x65\x72\x00\x00'):
        magic = "gfshader"
        file.seek(offset+32)
        bytedata2 = file.read(64)
        filename = bytedata2.decode("utf-8").strip('\x00')
        magic = filename+"."+magic
        OverrideFileName = True
    #is it a model?
    if(bytedata == b'\x67\x66\x6D\x6F\x64\x65\x6C\x00'):
        file.seek(offset)
        magic = "gfmodel"
        name = findFileNameGFModel(file)
        magic = name+"."+magic
        OverrideFileName = True
    #is it a environment file?
    if(bytedata0 == b'\x47\x46\x42\x45\x4E\x56\x00\x00'):
        file.seek(offset+92)
        bytedata2 = file.read(12)
        magic = "gfenv"
        name = bytedata2.decode("utf-8").strip('\x00')
        magic = name+"."+magic
        OverrideFileName = True
        
    file.seek(offset+8)
    bytedata3 = file.read(8)
    print(bytedata3)
    if(bytedata3 == b'texture\x00'):
        file.seek(offset+40)
        magic = "gftexture"
        bytedata4 = file.read(56)
        filename = bytedata4.decode("utf-8").strip('\x00')
        magic = filename+"."+magic
        OverrideFileName = True
        
    # is it a animation?
    file.seek(offset)
    bytedata5 = file.read(4)
    if(bytedata5 == b'\x00\x00\x06\x00'):
        magic = "gfanimation"
    
    if OverrideFileName == True:
        return magic
    else:
        return "."+magic 

                        
def DeleteExtras(listofindexes,masterlist):
    offset = 0
    for x in sorted(listofindexes, reverse=True):
        print("x")
        print(x)
        masterlist.pop(x)
        #offset is needed because when you remove something from the list, the position of the next index will decrease
        offset = offset + 1
        print(offset)



class GFFileSystem(object):

    def __init__(self,m,off):
        self.magic = m
        self.offset = off
        
   

        
        
        
    filepath = sys.argv[1]
    print(filepath)
    fs = open(filepath,'rb');
    arr = []
    directorytree = []
    LoadFS(fs,arr,0,[],0)
    global filestodelete
    DeleteExtras(filestodelete,arr)
    
    count = 0   
    for x in arr:
        count2 = 0
        for y in arr[count]:
            print(arr[count][count2])
            count2 = count2 + 1
        count = count + 1
        print("-----------------------")
    
    MakeDirs(arr,fs)
        
    fs.close()