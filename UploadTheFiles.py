#!/usr/bin/python3
# coding=utf-8

import paramiko
import hashlib
import getpass
import time
import threading
import os

hsh={}
curthread=0

def sftp_mkdir(remote):
    sf = paramiko.Transport((host,port))
    sf.connect(username = username,password = password)
    sftp = paramiko.SFTPClient.from_transport(sf)
    pos=-1
    for i in range(0,len(remote)):
        if remote[i] == "/":
            pos=i
    remote=remote[0:pos]
    print("Making directory "+remote+"...")
    try:
        sftp.stat(remote)
        print('Directory exists!')
    except:
        try:
            sftp.mkdir(remote)
            print('Mkdir of "'+remote+'" has finished!')
        except Exception as e:
            print("Mkdir exception: ",e)
    sf.close()
    
def sftp_upload(local,remote,filehsh):
    global curthread
    while curthread > maxthread:
        time.sleep(1)
    curthread=curthread+1
    print('Uploading file "'+local+'" to "'+remote+'"')
    sf = paramiko.Transport((host,port))
    sf.connect(username = username,password = password)
    sftp = paramiko.SFTPClient.from_transport(sf)
    try:
        sftp_mkdir(remote)
        sftp.put(local,remote)
        print('Upload of file "'+local+'" has finished!')
    except Exception as e:
        print('Upload exception:',e)
    sf.close()
    curthread=curthread-1

def upload(dir):
    l=os.listdir(dir)
    for f in l:
        path=dir+"/"+f
        if os.path.isdir(path):
            upload(path)
        else:
            hshtmp=hashlib.md5()
            with open(path, 'rb') as f:
                hshtmp.update(f.read())
            try:
                prehsh=hsh[path]
            except:
                prehsh="NULL"
            if prehsh != hshtmp.hexdigest():
                hsh[path]=hshtmp.hexdigest()
                if prehsh == "NULL":
                    print('\"'+path+'\" hasn\'t been uploaded before!')
                    print('Hash of "'+path+'" is '+hsh[path])
                else:
                    print('Detected changes in "'+path+'"!')
                    print('Pre-Hash of "'+path+'" is "'+prehsh+'".')
                    print('Cur-Hash of "'+path+'" is "'+hsh[path]+'".')
                thread=threading.Thread(target=sftp_upload,args=(path,remote+path.replace(local,""),hsh[path],))
                thread.start()

if __name__ == '__main__':
    while 1:
        try:
            host=input("Remote host:")
            break
        except:
            print("Invalid input! Input again!")
    while 1:
        try:
            port=int(input("Port:"))
            break
        except:
            print("Invalid input! Input again!")
    while 1:
        try:
            username=input("Username:")
            break
        except:
            print("Invalid input! Input again!")
    while 1:
        try:
            password=getpass.getpass()
            break
        except:
            print("Invalid input! Input again!")
    while 1:
        try:
            local=input("Local directory:")
            local=local.replace("\\", "/")
            if local[len(local)-1]=='/':
                local=local[0:len(local)-1]
            break
        except:
            print("Invalid input! Input again!")
    while 1:
        try:
            remote=input("Remote directory:")
            remote=remote.replace("\\", "/")
            if remote[len(remote)-1]=='/':
                remote=remote[0:len(remote)-1]
            break
        except:
            print("Invalid input! Input again!")
    while 1:
        try:
            maxthread=input("Max thread number (a number from 1 to 10):")
            if not maxthread.isdigit():
                print("Input a number!")
                continue
            maxthread=int(maxthread)
            if maxthread < 1 or maxthread > 10:
                print("Invalid number of max thread number! Input again!")
                continue
            break
        except:
            print("Invalid input! Input again!")
    print("Auto Upload System started!")
    sftp_mkdir(remote)
    while 1:
        upload(local)
        time.sleep(1)