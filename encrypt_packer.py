#!/usr/bin/python
# -*- coding=utf-8 -*-
import os
import sys
import tarfile
import random
import string
import subprocess
import stat

os.chdir(os.path.abspath(os.path.dirname(__file__)))
if len(sys.argv) != 4:
    print("Please \"command [from] [name] [public key]\"")
    sys.exit()
else:
    from_path = sys.argv[1]
    name = sys.argv[2]
    public_key = sys.argv[3]

f = open(public_key,"r")
public_key_data = f.read()
f.close()

key = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(192)])
encrypt_cmd = "openssl aes-256-cbc -salt -in %s -out %s.enc -pass pass:%s"

os.mkdir(name)
os.mkdir(name+"/libs")
if public_key_data.split(" ")[0] == "ssh-rsa":
    os.system("ssh-keygen -f %s -e -m PKCS8 > %s" % (public_key, name+"/libs/public_key"))
    public_key = name+"/libs/public_key"
else:
    f = open(name+"/libs/public_key","w")
    f.write(public_key)
    f.close()
os.system('echo "%s" | openssl rsautl -encrypt -pubin -inkey %s > %s/key' % (key, public_key, name+"/libs"))

tar_name = name + ".tar.gz"
archive = tarfile.open(tar_name, mode="w:gz")
archive.add(from_path)
archive.close()
os.system(encrypt_cmd % (name+".tar.gz", name+"/"+name, key))

configure_text = """#!/bin/bash
pub_key=`cat libs/public_key`
pubkey_filename=''
is_successful="false"
prv_pub_key_tmp=" "
for filename in `find ~/.ssh/ -maxdepth 1 -type f`; do
    if [[ `cat ${filename}` = *PRIVATE* ]] ; then
        ssh-keygen -y -f ${filename} > /tmp/public_key_tmp
        chmod 0600 /tmp/public_key_tmp
        prv_pub_key_tmp=`ssh-keygen -f /tmp/public_key_tmp -e -m PKCS8`
        if [[ ${pub_key} = ${prv_pub_key_tmp} ]]; then
            pubkey_filename=${filename}
            is_successful="true"
            break
        fi
    fi
done
if test ${is_successful} = "true"; then
    cat ${pubkey_filename} > libs/prvpath
    prv_pub_key_tmp=`cat libs/key | openssl rsautl -decrypt -inkey libs/prvpath`
    echo ${prv_pub_key_tmp} > libs/dec_key
fi
echo ".SILENT:" > Makefile
echo "decrypt:" >> Makefile
filepath=`ls *.enc`
echo "	mkdir desc" >> Makefile
echo "	openssl aes-256-cbc -d -in ${filepath} -out desc/%s -pass file:./libs/dec_key" >> Makefile
echo '	echo "Successful!! Show inside directory of [desc]"' >> Makefile
""" % tar_name
f = open(name+"/configure","w")
f.write(configure_text)
f.close()
os.chmod(name+"/configure", stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
tar_name = name + ".tar.gz"
archive = tarfile.open(tar_name, mode="w:gz")
archive.add(name)
archive.close()
