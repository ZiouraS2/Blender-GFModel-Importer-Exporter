import os
import sys

filecount = -1
filestodelete = []

def LoadFS(file,arr,offset,parent,recursion):
    global filecount
    global filestodelete
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
    #print()
    offsets = [None]*(numofoffsets+1)
    #allfound = False
        
        
    for number in range(numofoffsets + 1):
        offsets[number] = file.read(4)
            
    for number in range(numofoffsets):    
        #magic /folder
        filecount = filecount + 1
        arr.append([])
        arr[filecount].append(parent.copy())
        #print("appending magic")
        arr[filecount][0].append(magic1+magic2)
        #print("arr"+"["+str(filecount)+"]["+"0"+"]")
        #print(arr[filecount][0])
        #file number
        arr[filecount].append(number)
        #where to start reading
        arr[filecount].append(int.from_bytes(offsets[number],"little")+offset)
        #how long to read file for
        arr[filecount].append(int.from_bytes(offsets[number + 1],"little") - int.from_bytes(offsets[number],"little"))
        #print("filecount:")
        #print(filecount)
    
    print()
    
     
    #if we find subfolders
 
    if recursion < 1:
        for number in range(numofoffsets):
            #print("offset recursion:")
            #print(arr[number][2])
            file.seek(arr[number][2])
            testfile1 = int.from_bytes(file.read(1),"little");
            testfile2 = int.from_bytes(file.read(1),"little");  
            print("offset")           
            print(arr[number][2])
            print(number)
                
            if((testfile1 < 41 or testfile1 > 133) and (testfile2 < 41 or testfile2 > 133)):
                print("subfolder not found")
            else:         
                
                print("recursion path")
                print(arr[number][0])
                LoadFS(file,arr,arr[number][2],arr[number][0],recursion)
                
                #if we find a subfolder, we need to remove the original "file" we found it in
                #marking for deletion insead of actually deleting rn
                filestodelete.append(number)

                #filecount = filecount - 1
                
                print("filecount ")
                print(filecount)
                
        recursion = recursion + 1
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
            filename = str(MasterList[count][1])+filetype
            file.seek(MasterList[count][2])
            filedata = file.read(MasterList[count][3])
            with open(directory_name+filename, "wb") as file1:
                file1.write(filedata)
            count = count + 1
            
            
def checkFileType(offset,file):
    #skip first 16 bytes to check for gfsection
    magic = ".bin"
    file.seek(offset+16)
    magic = file.read(8).decode("utf-8");
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