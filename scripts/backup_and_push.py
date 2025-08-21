#!/usr/bin/env python3
from pathlib import Path
import tarfile, subprocess, datetime, os, sys
repo=Path('/home/ubuntu/agent-repo')
outdir=Path('/home/ubuntu/recovery')
outdir.mkdir(parents=True,exist_ok=True)
now=datetime.datetime.utcnow().strftime('%F')
archive=outdir/f'backup-{now}.tar.gz'
enc=outdir/f'backup-{now}.tar.gz.gpg'
with tarfile.open(archive,'w:gz') as tf:
    tf.add(repo,arcname='agent-repo')
# encrypt
passphrase='m4rr4n0'
subprocess.run(['gpg','--batch','--yes','--passphrase',passphrase,'-c','-o',str(enc),str(archive)])
# push to backups repo
pushdir='/home/ubuntu/tmp'
os.makedirs(pushdir,exist_ok=True)
# copy encrypted file into pushdir
pfile=Path(pushdir)/enc.name
subprocess.run(['cp',str(enc),str(pfile)])
# git add/commit/push
import shutil
if not Path(pushdir+'.git').exists():
    subprocess.run(['git','-C',pushdir,'init'])
    subprocess.run(['git','-C',pushdir,'remote','add','origin','git@github.com:anabelle/opencode-backups.git'])
subprocess.run(['git','-C',pushdir,'add',pfile.name])
subprocess.run(['git','-C',pushdir,'commit','-m',f'backup {now}'], stderr=subprocess.DEVNULL)
subprocess.run(['git','-C',pushdir,'push','-u','origin','master'])
print('backup and push done')
