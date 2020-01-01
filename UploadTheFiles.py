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

def log(s):
    if loglevel == "info" or loglevel == "error" and "exception" in s:
        print("["+time.strftime('%Y.%m.%d-%H:%M:%S')+"] "+s)
        if not logfile is None:
            logfile.write("["+time.strftime('%Y.%m.%d-%H:%M:%S')+"] "+s+"\n")

def sftp_mkdir(remote):
    pos=-1
    for i in range(0,len(remote)):
        if remote[i] == "/":
            pos=i
    remote=remote[0:pos]
    try:
        log("Making directory "+remote+"...")
        sf = paramiko.Transport((host,port))
        sf.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(sf)
        sftp.stat(remote)
        sf.close()
        log('Directory exists!')
        return 1
    except:
        try:
            sf = paramiko.Transport((host,port))
            sf.connect(username = username,password = password)
            sftp = paramiko.SFTPClient.from_transport(sf)
            sftp.mkdir(remote)
            sf.close()
            log('Mkdir of "'+remote+'" has finished!')
            return 1
        except Exception as e:
            log("Mkdir exception: "+str(e))
            return 0
    
def sftp_upload(local,remote,hshtmp):
    uploading.append(local)
    global curthread
    curthread=curthread+1
    try:
        log('Uploading file "'+local+'" to "'+remote+'"')
        sf = paramiko.Transport((host,port))
        sf.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(sf)
        while not sftp_mkdir(remote):
            time.sleep(1)
        sftp.put(local,remote)
        sf.close()
        hsh[local]=hshtmp
        with open("FileHashes/"+local.replace("/","_").replace(":","_")+".hsh","w") as f:
            f.write(hshtmp)
        log('Upload of file "'+local+'" has finished!')
    except Exception as e:
        hsh[local]="ERROR"
        log("Upload exception: "+e)
    curthread=curthread-1
    uploading.remove(local)

def sftp_remove(local,remote):
    global curthread
    curthread=curthread+1
    try:
        log('Removing file "'+remote+'"')
        sf = paramiko.Transport((host,port))
        sf.connect(username = username,password = password)
        sftp = paramiko.SFTPClient.from_transport(sf)
        sftp.remove(remote)
        sf.close()
        del hsh[local]
        os.remove("FileHashes/"+local.replace("/","_").replace(":","_")+".hsh")
        log('Removal of file "'+local+'" has finished!')
    except Exception as e:
        log("Removal exception: "+str(e))
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
        time.sleep(0.01)
        path=dir+"/"+f
        conti=0
        if ignored.count(path) > 0 or uploading.count(path) > 0:
            continue
        for ig in ignore:
            if path.find(ig) != -1:
                conti=1
                ignored.append(path)
                log("Ignoring "+path+".")
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
            prehsh="NULL"
            if hsh.keys().__contains__(path):
                prehsh=hsh[path]
            elif os.path.exists("FileHashes/"+path.replace("/","_").replace(":","_")+".hsh"):
                with open("FileHashes/"+path.replace("/","_").replace(":","_")+".hsh","r") as f:
                    prehsh=f.read()
            if prehsh != hshtmp.hexdigest():
                if prehsh == "NULL":
                    log('\"'+path+'\" hasn\'t been uploaded before!')
                    log('Hash of "'+path+'" is '+hshtmp.hexdigest())
                else:
                    log('Detected changes in "'+path+'"!')
                    log('Pre-Hash of "'+path+'" is "'+prehsh+'".')
                    log('Cur-Hash of "'+path+'" is "'+hshtmp.hexdigest()+'".')
                threading.Thread(target=sftp_upload,args=(path,remote+path.replace(local,""),hshtmp.hexdigest(),)).start()

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--conf", required=True, help="path to the JSON configuration file")
    args = vars(ap.parse_args())

    warnings.filterwarnings("ignore")
    conf = json.load(open(args["conf"]))
    
    if not conf.keys().__contains__("host"):
        print("Host name not specified! Exiting...")
        print("You can set host name with 'host' in the configuration.")
        exit(0)
    host=conf["host"]

    if not conf.keys().__contains__("port"):
        print("Port not specified. Using default 22.")
        print("You can configure port with 'port' in the configuration.")
        port=22
    else:
        port=conf["port"]
    try:
        port=int(port)
    except:
        print("Port must be an integer! Exiting...")
        exit(0)
        
    if not conf.keys().__contains__("username"):
        print("Remote machine username not specified! Exiting...")
        print("You can set it with 'username' in the configuration.")
        exit(0)
    username=conf["username"]

    if not conf.keys().__contains__("password"):
        print("Remote machine password not specified! Exiting...")
        print("You can set it with 'password' in the configuration.")
        exit(0)
    password=conf["password"]

    if not conf.keys().__contains__("local"):
        print("Local directory not specified! Exiting...")
        print("You can set local directory with 'local' in the configuration.")
        exit(0)
    local=conf["local"]
    local=local.replace("\\", "/")
    if local[len(local)-1]=='/':
        local=local[0:len(local)-1]

    if not conf.keys().__contains__("remote"):
        print("Remote directory not specified! Exiting...")
        print("You can set remote directory with 'remote' in the configuration.")
        exit(0)
    remote=conf["remote"]
    remote=remote.replace("\\", "/")
    if remote[len(remote)-1]=='/':
        remote=remote[0:len(remote)-1]

    if not conf.keys().__contains__("thread"):
        print("Thread number not specified. Using default 3.")
        print("You can configure it with 'thread' in the configuration.")
        maxthread="3"
    else:
        maxthread=conf["thread"]
    try:
        maxthread=int(maxthread)
    except:
        print("Thread number must be an integar!")
        exit()
    if maxthread < 1 or maxthread > 10:
        print("Invalid thread number!")
        print("It must be a number between 1 and 10.")
        exit(0)

    if not conf.keys().__contains__("loglevel"):
        print("Loglevel not specified. Using default 'info'.")
        print("You can configure it with 'loglevel' in the configuration.")
        loglevel="info"
    else:
        loglevel=conf["loglevel"]
    if loglevel != "info" and loglevel != "error" and loglevel != "none":
        print("Invalid loglevel!")
        print("Loglevel must be 'info', 'error' or 'none'")
        exit(0)
    if loglevel == "none":
        logfile=None
    else:
        logfile=open("UploadTheFiles.log","a")

    ignore=conf["ignore"].replace("\\","/").split("|")
    for i in range(0,len(ignore)):
        if ignore[i][len(ignore[i])-1]=='/':
            ignore[i]=ignore[i][0:len(ignore)-1]

    if not os.path.exists("FileHashes"):
        os.mkdir("FileHashes")
    if not os.path.isdir("FileHashes"):
        os.remove("FileHashes")
        os.mkdir("FileHashes")
    log("Auto Upload System started!")
    sftp_mkdir(remote)
    while 1:
        upload(local)
        time.sleep(1)