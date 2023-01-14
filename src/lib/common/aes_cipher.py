import os
import json
import argparse
import sys
import traceback

from hashlib import md5
from base64 import b64decode, b64encode
from Crypto.Cipher import AES


default_master_key = '8f8695cc51224717a0b4f94473bce491'
pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]

class AESCipher:
    """
    AES 암복호화를 위한 클래스로 IV 가 없는 ECB 모드를 사용한다.
    """
    def __init__(self, key = default_master_key, encode = True):
        if encode:
            # AES256 사용하기 위해 입력받은 키를 256bit로 변경
            self.key = md5(key.encode('utf8')).hexdigest()
        else:
            self.key = key

    #region Encrypt

    def encrypt(self, raw):
        raw = pad(raw)
        cipher = AES.new(self.key, AES.MODE_ECB)
        return b64encode(cipher.encrypt(raw.encode('utf8')))

    def encrypt_to_file(self, raw, path):
        with open(path, 'wb') as enc_file:
            enc_file.write(self.encrypt(raw))

    def encrypt_file(self, from_path, to_path):
        if os.path.exists(from_path):
            with open(from_path, 'r') as f:
                self.encrypt_to_file(f.read(), to_path)

    #endregion Encrypt

    #region Decrypt

    def decrypt(self, enc):
        enc = b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_ECB)
        return unpad(cipher.decrypt(enc)).decode('utf8')

    def decrypt_file(self, from_path, to_path):
        if os.path.exists(from_path):
            with open(to_path, 'w') as f:
                f.write(self.decrypt_from_file(from_path))

    def decrypt_from_file(self, path):
        plaintext = ''
        if os.path.exists(path):
            with open(path, 'rb') as enc_file:
                plaintext = self.decrypt(enc_file.read())
        return plaintext


    def decrypt_file_to_json(self, path):
        return json.loads(self.decrypt_from_file(path).replace('\'', '"'))

    #endregion Decrypt        


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-m', '--mode', default='enc', help='enc or dec')
        parser.add_argument('-i', '--file_in')
        parser.add_argument('-o', '--file_out')
        parser.add_argument('-k', '--key')
        args = parser.parse_args()

        aes_cipher = AESCipher(default_master_key if args.key == None else args.key)
        if args.mode == 'enc':
            aes_cipher.encrypt_file(args.file_in, args.file_out)

        elif args.mode == 'dec':
            aes_cipher.decrypt_file(args.file_in, args.file_out)
            
    except:
        print('ERROR occured.{}'.format(traceback.format_exc()))
        sys.exit(2)
            

