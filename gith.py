#!/usr/bin/python
"""
Utility for git repos with basic encryption.
"""

import os
import sys
import shutil
from os.path import getmtime
from ConfigParser import ConfigParser
from ncrypt.cipher import EncryptCipher, DecryptCipher, CipherType

# TODO support for dirs here
DO_NOT_ENCRYPT = ['.gitignore']

# TODO gitignore support
IGNORE_FILES = ['.gith']
IGNORE_DIRS = ['.git']

# The directory that git init creates
GIT_DIR = '.git'
GITH_CONFIG = '.gith'
CIPHER_TYPE = CipherType('AES-128', 'CBC')

def encrypt_file(cipherType, key, iv, src, dest):
    in_file = open(src, 'r')
    out_file = open(dest, 'w')

    enc = EncryptCipher( cipherType, key, iv )
    while 1 :
        data = in_file.read( 8192 )
        if not data : break
        out_data = enc.update( data )
        out_file.write( out_data )
    final_data = enc.finish()
    out_file.write( final_data )

    in_file.close()
    out_file.close()

def decrypt_file( cipherType, key, iv, in_file, out_file ) :
    dec = DecryptCipher( cipherType, key, iv )
    while 1 :
        data = in_file.read( 8192 )
        if not data : break
        out_data = dec.update( data )
        out_file.write( out_data )
    final_data = dec.finish()
    out_file.write( final_data )

def read_config():
    config = ConfigParser()
    config.readfp(open(GITH_CONFIG))
    d = {}
    for section in config.sections():
        for key, val in config.items(section):
            d[key] = val
    return d
    

def touch(path, val):
    with file(path, 'a'):
        os.utime(path, (val, val))

def sync(cfg):
    """Copies and encrypts files if they've been modified"""
    work_dir = cfg['working_dir']
    enc_dir = cfg['encrypted_dir']

    if not os.path.isdir(enc_dir):
        print 'Creating %s' % enc_dir
        os.mkdir(enc_dir)

    for dirname, dirnames, filenames in os.walk(work_dir):
        """
        for subdir in dirnames:
            if not os.path.isdir(subdir):
                # TODO fix this -- add support for subdirectories
                os.mkdir(enc_dir + subdir)
        """

        for src in filenames:
            dest = os.path.join(enc_dir, src)
            modified = getmtime(src)
            if src not in IGNORE_FILES and \
                (not os.path.isfile(dest) or modified != getmtime(dest)):
                if src in DO_NOT_ENCRYPT:
                    # just copy it
                    shutil.copyfile(src, dest)                    
                else:
                    # encrypt
                    print 'Encrypting %s' % src
                    encrypt_file(CIPHER_TYPE, cfg['key'], cfg['iv'], src, dest)

                # synchronize modified time
                touch(dest, modified)

        break

def duplicate(cfg, argv=sys.argv[1:]):
    """Duplicates git command to second encrypted repo"""
    cmd = 'git ' + ' '.join(argv)
    os.system(cmd)

    if argv[0] == 'commit':
        # copy edit message
        # TODO make it so that this doesn't have to be entered twice
        editpath = os.path.join(GIT_DIR, 'COMMIT_EDITMSG')
        shutil.copyfile(os.path.join(cfg['working_dir'], editpath), \
            os.path.join(cfg['encrypted_dir'], editpath))

    os.chdir(cfg['encrypted_dir'])
    os.system(cmd)

def main(argv=sys.argv):
    cfg = read_config()
    sync(cfg)
    duplicate(cfg)

if __name__ == "__main__":
    main()
