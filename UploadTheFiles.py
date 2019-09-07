#!/usr/bin/python3
# coding=utf-8

import paramiko
import hashlib
import getpass
import time
import threading
import os
import json
import argparse
import warnings

hsh={}
fs={} # files
ignored=[]
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
    
def sftp_upload(local,remote):
    global curthread
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

def sftp_remove(remote):
    global curthread
    curthread=curthread+1
    print('Removing file "'+remote+'"')
    sf = paramiko.Transport((host,port))
    sf.connect(username = username,password = password)
    sftp = paramiko.SFTPClient.from_transport(sf)
    try:
        sftp.remove(remote)
        print('Removal of file "'+local+'" has finished!')
    except Exception as e:
        print('Removal exception:',e)
    sf.close()
    curthread=curthread-1

def upload(dir):
    l=os.listdir(dir)
    try:
        if fs[dir] != '':
            for f in fs[dir]:
                path=f
                if not os.path.exists(path):
                    while curthread > maxthread:
                        time.sleep(0.1)
                    sftp_remove(remote+path.replace(local,""))
                    fs.remove(f)
    except:
        fs[dir]=[]
    for f in l:
        path=dir+"/"+f
        conti=0
        if ignored.count(path) > 0:
            continue
        for ig in ignore:
            if path.find(ig) != -1:
                conti=1
                ignored.append(path)
                print("Ignoring "+path+".")
                break
        if conti:
            continue
        if fs[dir].count(dir+"/"+f) == 0:
            fs[dir].append(dir+"/"+f)
        while curthread > maxthread:
            time.sleep(0.1)
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
                thread=threading.Thread(target=sftp_upload,args=(path,remote+path.replace(local,""),))
                thread.start()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
    args = vars(ap.parse_args())

    warnings.filterwarnings("ignore")
    conf = json.load(open(args["conf"]))
    
    host=conf["host"]
    if host is None:
        print("Invalid host!")
    port=conf["port"]
    if port is None:
        print("Invalid port!")
    post=int(port)
    username=conf["username"]
    if username is None:
        print("Invalid username!")
    password=conf["password"]
    if password is None:
        print("Invalid password!")
    local=conf["local"]
    if local is None:
        print("Invalid local directory!")
    local=local.replace("\\", "/")
    if local[len(local)-1]=='/':
        local=local[0:len(local)-1]
    remote=conf["remote"]
    if remote is None:
        print("Invalid remote directory!")
    remote=remote.replace("\\", "/")
    if remote[len(remote)-1]=='/':
        remote=remote[0:len(remote)-1]
    maxthread=conf["thread"]
    if maxthread is None:
        print("Invalid thread!")
    maxthread=int(maxthread)
    if maxthread < 1 or maxthread > 10:
        print("Invalid number of max thread number!")
        exit(0)
    ignore=conf["ignore"].replace("\\","/").split("|")
    for i in range(0,len(ignore)):
        if ignore[i][len(ignore[i])-1]=='/':
            ignore[i]=ignore[i][0:len(ignore)-1]
    print("Auto Upload System started!")
    sftp_mkdir(remote)
    while 1:
        upload(local)
        time.sleep(1)