"""
Module providing AES256 symmetric encryption services

If run as a Python command-line script, module will interactively prompt
for a password, then print out the corresponding encoded db_config.ini
password parameters suitable for cut/pasting into API .ini config files.

Copyright (C) 2016 ERT Inc.
"""
import getpass

from Crypto.Cipher import AES
from Crypto.Util import Padding #Requires PyCrypto v2.7+
from Crypto import Random

__author__ = "Brandon J. Van Vaerenbergh <brandon.vanvaerenbergh@noaa.gov>, "

def encode(plaintext_string, key, salt):
    """
    AES256 encrypts a string, using provided key & 128bit salt

    The first 128bits of the returned ciphertext is an exact copy of the
    provided salt (to facilitate decryption). To store salt separately
    from the actual ciphertext, simply split off the first 128bits.

    Keyword Parameter:
    plaintext_string  -- String to be enciphered.
    key  -- Bytes, representing an 256bit AES private key.
    salt  -- Bytes, representing a randomly generated (one-time-use),
      128bit long AES Initialization Vector which will be used to salt
      the resulting ciphertext.

    >>> key = (b'\\x02\\xd2d\\xfb\\x84Q\\xed?\\x92\\xda\\xcd\\x9a/)'
    ...        b'\\x15\\xdc\\xb5~\\\\\\x03\\xeby\\xa7\\xfb&#\\xb8'
    ...        b'\\xd1y+a\\x86')
    >>> s = b'\\x94\\x99$y\\x83B\\x85N\\x94E\\x01L\\xe5\\xba\\xea\\xdf'
    >>> encode("Hello, World!", key, s)
    b'\\x94\\x99$y\\x83B\\x85N\\x94E\\x01L\\xe5\\xba\\xea\\xdf\\t\\xbc\\x84\\xf8L\\xd5adz\\x1bl\\x9f\\x9c\\x1db\\xb1'
    """
    assert len(key) >= 256/8, "Private key must be 256bit, minimum"
    assert len(salt) == 128/8, "Expected (exactly) 128bit long salt"
    #per dlitz.net/software/pycrypto/api/current/Crypto.Cipher.AES-module.html
    aes256_cbc = AES.new(key, AES.MODE_CBC, IV=salt)
    # PKCS#7 CMS pad the input(AES requires input length as multiple of 16 bit)
    try:
        plaintext_bytes = plaintext_string.encode('utf-8')
    except AttributeError:
        plaintext_bytes = plaintext_string #Seems like it's already bytes
    padded_plaintext = Padding.pad(plaintext_bytes, 16, style='pkcs7')
    ciphertext = aes256_cbc.encrypt(padded_plaintext)
    # store our known-length iv for reuse,by simply prepending to ciphertext
    return salt + ciphertext #(safe to do) salt just stops rainbow table

def decode(salted_ciphertext_bytes, key):
    """
    Decrypts an AES256 enciphered String via provided key & 128bit salt

    Keyword Parameter:
    salted_ciphertext_bytes  -- Bytes, representing a randomly generated
      (one-time-use) 128bit long AES Initialization Vector & an AES256
      encyphered String which was salted with the one-time IV. The first
      128bits of 'salted_ciphertext_bytes' represent the salt, with
      remainder containing the encoded cyphertext.
    key  -- Bytes, representing an 256bit AES private key.

    >>> key = (b'\\x02\\xd2d\\xfb\\x84Q\\xed?\\x92\\xda\\xcd\\x9a/)'
    ...        b'\\x15\\xdc\\xb5~\\\\\\x03\\xeby\\xa7\\xfb&#\\xb8'
    ...        b'\\xd1y+a\\x86')
    >>> ciphertext = (b'\\x94\\x99$y\\x83B\\x85N\\x94E\\x01L\\xe5\\xba'
    ...               b'\\xea\\xdf\\t\\xbc\\x84\\xf8L\\xd5adz\\x1bl'
    ...               b'\\x9f\\x9c\\x1db\\xb1')
    >>> decode(ciphertext, key)
    'Hello, World!'
    """
    assert len(key) >= 256/8, "Private key must be 256bit, minimum"
    # per convention for this Module, the first 128 ciphertext bits represent
    # the randomly generated Initialization Vector used during encryption
    salt_byte_length = int(128/8)
    salt = salted_ciphertext_bytes[:salt_byte_length]
    ciphertext = salted_ciphertext_bytes[salt_byte_length:]
    #per dlitz.net/software/pycrypto/api/current/Crypto.Cipher.AES-module.html
    aes256_cbc = AES.new(key, AES.MODE_CBC, IV=salt)
    padded_plaintext_bytes = aes256_cbc.decrypt(ciphertext)
    plaintext_bytes = Padding.unpad(padded_plaintext_bytes, 16, style='pkcs7')
    return plaintext_bytes.decode('utf-8')

def interactive_mode():
    """
    Command-line password entry+confirmation prompt,prints encoded form
    """
    pw1 = getpass.getpass("Enter db connection password: ")
    pw2 = getpass.getpass("Re-enter password, to confirm: ")
    if pw1 != pw2:
        print("ERROR: Passwords do not match, try again.")
        interactive_mode()
    # use appears to have accurately entered the pw. Now encrypt.
    random_bytes = Random.new()
    key_length_bytes = int(256/8)
    salt_length_bytes = int(128/8)
    one_time_key = random_bytes.read(key_length_bytes)
    one_time_salt = random_bytes.read(salt_length_bytes)
    ciphertext = encode(pw1, one_time_key, one_time_salt)
    msg = 'Warehouse API .ini password parameters (paste both into .ini file):'
    print(msg)
    print('ciphertext_key = {}'.format(one_time_key))
    print('ciphertext = {}'.format(ciphertext))
    exit(0)
    
if __name__ == '__main__':
    interactive_mode()
