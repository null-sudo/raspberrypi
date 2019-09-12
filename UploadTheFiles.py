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
uploading=[]
ignored=[]
curthread=0

def newprint(s):
    print("["+time.strftime('%Y.%m.%d-%H:%M:%S')+"] "+s)

def sftp_mkdir(remote):
    
    pos=-1
    for i in range(0,len(remote)):
        if remote[i] == "/":
            pos=i
    remote=remote[0:pos]
    try:
        newprint("Making directory "+remote+"...")
        sf = paramiko.Transport((host,port))
        sf.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(sf)
        sftp.stat(remote)
        sf.close()
        newprint('Directory exists!')
    except:
        try:
            sf = paramiko.Transport((host,port))
            sf.connect(username = username,password = password)
            sftp = paramiko.SFTPClient.from_transport(sf)
            sftp.mkdir(remote)
            sf.close()
            newprint('Mkdir of "'+remote+'" has finished!')
        except Exception as e:
            print("["+time.strftime('%Y.%m.%d-%H:%M:%S')+"] Mkdir exception: ",e)
    
def sftp_upload(local,remote,hshtmp):
    uploading.append(local)
    global curthread
    curthread=curthread+1
    try:
        newprint('Uploading file "'+local+'" to "'+remote+'"')
        sf = paramiko.Transport((host,port))
        sf.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(sf)
        sftp_mkdir(remote)
        sftp.put(local,remote)
        sf.close()
        hsh[local]=hshtmp
        newprint('Upload of file "'+local+'" has finished!')
    except Exception as e:
        hsh[local]="ERROR"
        print("["+time.strftime('%Y.%m.%d-%H:%M:%S')+"] Upload exception: ",e)
    curthread=curthread-1
    uploading.remove(local)

def sftp_remove(local,remote):
    global curthread
    curthread=curthread+1
    try:
        newprint('Removing file "'+remote+'"')
        sf = paramiko.Transport((host,port))
        sf.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(sf)
        sftp.remove(remote)
        sf.close()
        hsh[local]=""
        newprint('Removal of file "'+local+'" has finished!')
    except Exception as e:
        print("["+time.strftime('%Y.%m.%d-%H:%M:%S')+"] Removal exception: ",e)
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
                    sftp_remove(path,remote+path.replace(local,""))
                    fs.remove(f)
    except:
        fs[dir]=[]
    for f in l:
        path=dir+"/"+f
        conti=0
        if ignored.count(path) > 0 or uploading.count(path) > 0:
            continue
        for ig in ignore:
            if path.find(ig) != -1:
                conti=1
                ignored.append(path)
                newprint("Ignoring "+path+".")
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
                if prehsh == "NULL":
                    newprint('\"'+path+'\" hasn\'t been uploaded before!')
                    newprint('Hash of "'+path+'" is '+hshtmp.hexdigest())
                else:
                    newprint('Detected changes in "'+path+'"!')
                    newprint('Pre-Hash of "'+path+'" is "'+prehsh+'".')
                    newprint('Cur-Hash of "'+path+'" is "'+hshtmp.hexdigest()+'".')
                thread=threading.Thread(target=sftp_upload,args=(path,remote+path.replace(local,""),hshtmp.hexdigest(),))
                thread.start()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
    args = vars(ap.parse_args())

    warnings.filterwarnings("ignore")
    conf = json.load(open(args["conf"]))
    
    host=conf["host"]
    if host is None:
        newprint("Invalid host!")
    port=conf["port"]
    if port is None:
        newprint("Invalid port!")
    post=int(port)
    username=conf["username"]
    if username is None:
        newprint("Invalid username!")
    password=conf["password"]
    if password is None:
        newprint("Invalid password!")
    local=conf["local"]
    if local is None:
        newprint("Invalid local directory!")
    local=local.replace("\\", "/")
    if local[len(local)-1]=='/':
        local=local[0:len(local)-1]
    remote=conf["remote"]
    if remote is None:
        newprint("Invalid remote directory!")
    remote=remote.replace("\\", "/")
    if remote[len(remote)-1]=='/':
        remote=remote[0:len(remote)-1]
    maxthread=conf["thread"]
    if maxthread is None:
        newprint("Invalid thread!")
    maxthread=int(maxthread)
    if maxthread < 1 or maxthread > 10:
        newprint("Invalid number of max thread number!")
        exit(0)
    ignore=conf["ignore"].replace("\\","/").split("|")
    for i in range(0,len(ignore)):
        if ignore[i][len(ignore[i])-1]=='/':
            ignore[i]=ignore[i][0:len(ignore)-1]
    newprint("Auto Upload System started!")
    sftp_mkdir(remote)
    while 1:
        upload(local)
        time.sleep(1)