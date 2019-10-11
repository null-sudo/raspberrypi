#!/usr/bin/env python3
# coding=utf-8
# Copyright © 2018-2019 XiyuWang All rights reserved.
# RaspberryPi System Backup Script
import os
import sys

print("Importing packages...")
try:
    import pexpect
except:
    print("Installing pexpect...")
    os.system("sudo pip3 install pexpect")
    try:
        import pexpect
    except:
        print("[ERROR] Unable to install pexpect!")
        exit(0)
try:
    import subprocess
except:
    print("Installing subprocess...")
    os.system("sudo pip3 install subprocess")
    try:
        import subprocess
    except:
        print("[ERROR] Unable to install subprocess!")
        exit(0)
try:
    import getpass
except:
    print("Installing getpass...")
    os.system("sudo pip3 install getpass")
    try:
        import getpass
    except:
        print("[ERROR] Unable to install getpass!")
        exit(0)

print("\nRaspberryPi System Backup Script")
print("Copyright (C) 2019 XiyuWang All rights reserved.")
user=getpass.getuser()
print(user+", before you run this script, you should make sure the things below!")
print("1.You should run this script in Linux and in sudo mode")
print("2.You should run this script with \"python3\"")
print("3.You should insert only one SD card into the computer.")
print("4.Your computer should have enough disk space.")
print("5.Your computer will not shutdown during the backup.")
if input("If you are ready, press y to continue.") != "y":
    print("Exiting...")
    exit()

print("\nInstalling dosfstools,dump,parted,kpartx,progress...")
os.system("sudo apt-get install dosfstools dump parted kpartx progress")

print("\nCreating workspace folder...")
os.system("sudo mkdir backupimg")
os.chdir("backupimg")
os.system("sudo mkdir src_boot src_root tgt_boot tgt_root")

print("\nUnmounting all devices...")
os.system("sudo umount /dev/sd*")

print("\nFinding your RaspberryPi SD Card...")
deviceid="null"
for i in range(0,25):
    i=chr(i+ord("a"))
    if not os.path.exists("/dev/sd"+i) or not os.path.exists("/dev/sd"+i+"1") or not os.path.exists("/dev/sd"+i+"2"):
        continue
    deviceid="/dev/sd"+i
    os.system("sudo mount -t vfat -o uid="+user+",gid="+user+",umask=0000 "+deviceid+"1 ./src_boot/")
    os.system("sudo mount -t ext4 "+deviceid+"2 ./src_root/")
    if not os.path.exists("src_boot/kernel.img"):
        continue
    print("Detected RaspberryPi sd Card: "+deviceid)
if deviceid == "null":
    print("Unable to find the RaspberryPi SD Card!")
    print("Please check if you have inserted the card properly!")
    exit(0)

print("\nGetting RaspberryPi Hostname...")
name="raspberrypi.img"
with open("src_root/etc/hostname","r") as f:
    name=f.read().replace("\n","")+".img"
print("The image file will be saved as "+name)

print("\nGetting disk status...")
used=0
lines=os.popen("sudo df -h -B M")
for line in lines:
    if line.find(deviceid+"1") != -1:
        used=used+int(line.split()[2].replace("M",""))
    if line.find(deviceid+"2") != -1:
        used=used+int(line.split()[2].replace("M",""))
print("Used disk space:"+str(used))
used=used+200

print("\nGenerating image file...")
os.system("sudo dd if=/dev/zero of="+name+" bs=1M count="+str(used)+" status=progress")

print("\nParting img file...")
os.system("sudo parted "+name+" --script -- mklabel msdos")
os.system("sudo parted "+name+" --script -- mkpart primary fat32 8192s 122479s")
os.system("sudo parted "+name+" --script -- mkpart primary ext4 122880s -1")

print("\nMounting image file to loop device...")
p=subprocess.Popen("sudo losetup -f --show "+name,shell=True,stdout=subprocess.PIPE)
out,err=p.communicate()
loop=str(out).replace("b'","").replace("\\n'","")
os.system("sudo kpartx -va "+loop)

print("\nFormatting image file...")
loopid=loop.replace("/dev/loop","")
os.system("sudo mkfs.vfat -n boot /dev/mapper/loop"+loopid+"p1")
os.system("sudo mkfs.ext4 /dev/mapper/loop"+loopid+"p2")

print("\nMounting image file to workspace...")
os.system("sudo mount -t vfat -o uid="+user+",gid="+user+",umask=0000 /dev/mapper/loop"+loopid+"p1 ./tgt_boot/")
os.system("sudo mount -t ext4 /dev/mapper/loop"+loopid+"p2 ./tgt_root")

print("\nCopying files...(This may take several minutes)")
os.system("sudo rm -rf ./tgt_boot/*")
os.system("sudo cp -rfp ./src_boot/* ./tgt_boot/")
os.system("sudo chmod 777 tgt_root")
os.system("sudo chown "+user+"."+user+" tgt_root")
os.system("sudo rm -rf ./tgt_root/*")
os.chdir("tgt_root/")
p=subprocess.Popen("sudo dump -0uaf - ../src_root/ | sudo restore -rf -",shell=True,stdout=subprocess.PIPE)
os.chdir("..")
out,err=p.communicate()
if str(err) != "None":
    print("Trying tar...(This may take a long time)")
    os.system("sudo chmod 777 tgt_root")
    os.system("sudo chown "+name+"."+name+" tgt_root")
    os.system("sudo rm -rf ./tgt_root/*")
    os.chdir("src_root")
    p=subprocess.Popen("sudo tar pcf ../backup.tar",shell=True,stdout=subprocess.PIPE)
    out,err=p.communicate()
    if str(err) != "None":
        print("Backup failed!")
        print("Exiting...")
        exit(0)
    os.chdir("../tgt_root/")
    p=subprocess.Popen("sudo tar pxf ../backup.tar",shell=True,stdout=subprocess.PIPE)
    out,err=p.communicate()
    if str(err) != "None":
        print("Backup failed!")
        print("Exiting...")
        exit(0)
    os.chdir("..")
    os.system("sudo rm backup.tar")

print("\nFinishing...")
lines=os.popen("sudo blkid")
id="NULL"
for line in lines:
    if line.find("/dev/mapper/loop"+loopid+"p1") != -1:
        pos=line.find("PARTUUID")
        id=line[pos+10:pos+10+8]
print("PARTUUID="+id)
targetstr="PARTUUID="
f=open("tgt_boot/cmdline.txt","r")
lines=f.readlines()
f.close()
f=open("tgt_boot/cmdline.txt","w")
for line in lines:
    pos=line.find("PARTUUID=")
    if pos != -1:
        line=line.replace(line[pos+9:pos+9+8],id)
    f.write(line+"\n")
f.close()
f=open("tgt_root/etc/fstab","r")
lines=f.readlines()
f.close()
f=open("tgt_root/etc/fstab","w")
for line in lines:
    pos=line.find("PARTUUID=")
    if pos != -1:
        line=line.replace(line[pos+9:pos+9+8],id)
    f.write(line+"\n")
f.close()
os.system("sudo umount src_boot/ src_root/ tgt_boot/ tgt_root/")
os.system("sudo kpartx -d "+loop)
os.system("sudo losetup -d "+loop)
os.system("sudo eject "+deviceid)
os.chdir("..")
os.system("sudo mv backupimg/"+name+" "+name)
os.system("sudo rm -rf backupimg/")
print("\nBackup Finished!")
print("\nThe image file is saved as "+name)