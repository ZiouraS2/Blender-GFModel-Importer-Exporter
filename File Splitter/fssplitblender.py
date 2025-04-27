import os
import sys

filecount = -1
filestodelete = []
currentfirstlevelfile = 0


def LoadFS(file,arr,offset,parent,recursion):
    global filecount
    global filestodelete
    global currentfirstlevelfile
    #print("offset:")
    #print(offset) 
    #print("filecount:")
    #print(filecount)
    initfilecount = filecount
    file.seek(offset)
    magic1 = file.read(1).decode("utf-8");
    magic2 = file.read(1).decode("utf-8");     
    numofoffsets = int.from_bytes(file.read(2),"little")
    #print(numofoffsets)
    #print(magic1)
    #print(magic2)
    #print(offset)
    offsets = [None]*(numofoffsets+1)
    #allfound = False
        
        
    for number in range(numofoffsets + 1):
        offsets[number] = file.read(4)
    
    for number in range(numofoffsets):    
        #magic /folder
        filecount = filecount + 1
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
        #if(filecount < 98):
            #print(offsets[number])
            #print(int.from_bytes(offsets[number],"little")+offset)
        arr[filecount].append(int.from_bytes(offsets[number],"little")+offset)
        #if(filecount < 98):
            #print(filecount)
            #print(number)
            #print(arr[filecount][2])
        
        #how long to read file for[3]
        arr[filecount].append(int.from_bytes(offsets[number + 1],"little") - int.from_bytes(offsets[number],"little"))
        
        #print("filecount:")
    
    print(arr[0][2])
    
    
    
     
    #if we find subfolders
 
    if recursion < 1:
        for number in range(numofoffsets):
            #print("offset recursion:")
            #print(arr[number][2])
            file.seek(arr[number][2])
            testfile1 = int.from_bytes(file.read(1),"little");
            testfile2 = int.from_bytes(file.read(1),"little");  

                
            if((testfile1 < 41 or testfile1 > 133) and (testfile2 < 41 or testfile2 > 133)):
                print("subfolder not found")
            else:         
                #if(filecount < 98):
                    #print("recursion path")
                    #print(arr[number][0])
                    #print(arr[number][2])
                print()
                recursion = recursion + 1
                LoadFS(file,arr,arr[number][2],arr[number][0],recursion)
                
                #if we find a subfolder, we need to remove the original "file" we found it in
                #marking for deletion insead of actually deleting rn
                filestodelete.append(number)

                #filecount = filecount - 1
                
                print("filecount ")
                print(filecount)
            currentfirstlevelfile = currentfirstlevelfile + 1
                
        
    else:
        for number in range(numofoffsets):
            print("offset recursion > 1:")
            print(initfilecount)
            print(arr[initfilecount+number][2])
            file.seek(arr[initfilecount+number][2])
            testfile1 = int.from_bytes(file.read(1),"little");
            testfile2 = int.from_bytes(file.read(1),"little");  
                
            if((testfile1 < 41 or testfile1 > 133) and (testfile2 < 41 or testfile2 > 133)):
                print("subfolder not found")
            else:                    
                              
                LoadFS(file,arr,arr[initfilecount+number][2],arr[initfilecount+number][0],recursion)
                
                #if we find a subfolder, we need to remove the original "file" we found it in
                #marking for deletion insead of actually deleting rn
                filestodelete.append(number)

                #filecount = filecount - 1
                
                print("filecount ")
                print(filecount)
                    
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
                os.mkdir(directory_name)
                print(f"Directory '{directory_name}' created successfully.")
            except FileExistsError:
                print(f"Directory '{directory_name}' already exists.")
            except PermissionError:
                print(f"Permission denied: Unable to create '{directory_name}'.")
            except Exception as e:
                print(f"An error occurred: {e}")
                
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

    file.seek(offset+16)
    bytedata = file.read(8)
    
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
    for x in listofindexes:
        print("x")
        print(x)
        masterlist.pop(x-offset)
        #offset is needed because when you remove something from the list, the position of the next index will decrease
        offset = offset + 1



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