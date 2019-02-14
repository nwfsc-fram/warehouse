/* Java source, providing an AES encryption object
 * via: https://gist.github.com/dweymouth/11089238
 * ----------------------------------------------------------------------------
 * "THE BEER-WARE LICENSE" (Revision 42):
 * <dweymouth@gmail.com> wrote this file. As long as you retain this notice you
 * can do whatever you want with this stuff. If we meet some day, and you think
 * this stuff is worth it, you can buy me a beer in return.  D. Weymouth 4/2014
 * ----------------------------------------------------------------------------
 *
 * Copyright (C) 2014, 2016 D. Weymouth, ERT Inc.
 */
package gov.noaa.nwfsc.pentaho.encryption;

import java.io.*;
import java.security.*;
import java.security.spec.*;
import java.util.*;

import javax.crypto.*;
import javax.crypto.spec.*;

/**
 * A class to perform password-based AES encryption and decryption in CBC mode.
 * 128, 192, and 256-bit encryption are supported, provided that the latter two
 * are permitted by the Java runtime's jurisdiction policy files.
 * <br/>
 * The public interface for this class consists of the static methods
 * {@link #encrypt} and {@link #decrypt}, which encrypt and decrypt arbitrary
 * streams of data, respectively.
 */
public class AES {

	// AES specification - changing will break existing encrypted streams!
	private static final String CIPHER_SPEC = "AES/CBC/PKCS5Padding";

	// Process input/output streams in chunks - arbitrary
	private static final int BUFFER_SIZE = 1024;

	/**
	 * Encrypts a stream of data. The encrypted stream consists of a header
	 * followed by the raw AES data. The header is broken down as follows:<br/>
	 * <ul>
	 *   <li><b>keyLength</b>: AES key length in bytes (valid for 16, 24, 32) (1 byte)</li>
	 *   <li><b>IV</b>: pseudorandom AES initialization vector (16 bytes)</li>
	 * </ul>
	 *
	 * @param key
	 *   key to use for encryption (must be 128, 192, or 256 bytes in length)
	 * @param input
	 *   an arbitrary byte stream to encrypt
	 * @param output
	 *   stream to which encrypted data will be written
	 * @throws AES.InvalidKeyLengthException
	 *   if keyLength is not 128, 192, or 256
	 * @throws AES.StrongEncryptionNotAvailableException
	 *   if keyLength is 192 or 256, but the Java runtime's jurisdiction
	 *   policy files do not allow 192- or 256-bit encryption
	 * @throws IOException
	 */
	public static void encrypt(byte[] key, InputStream input, OutputStream output)
			throws InvalidKeyLengthException, StrongEncryptionNotAvailableException, IOException {
		// Check validity of key length
		int keyBitLength = key.length * 8;
		if (keyBitLength != 128 && keyBitLength != 192 && keyBitLength != 256) {
			throw new InvalidKeyLengthException(keyBitLength);
		}
		
		// initialize AES encryption
		Cipher encrypt = null;
		try {
			encrypt = Cipher.getInstance(CIPHER_SPEC);
			encrypt.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"));
		} catch (NoSuchAlgorithmException | NoSuchPaddingException impossible) { }
		  catch (InvalidKeyException e) { // 192 or 256-bit AES not available
			throw new StrongEncryptionNotAvailableException(keyBitLength, e);
		}
		
		// get initialization vector
		byte[] iv = null;
		try {
			iv = encrypt.getParameters().getParameterSpec(IvParameterSpec.class).getIV();
		} catch (InvalidParameterSpecException impossible) { }
		
		// write authentication and AES initialization data
		output.write((byte)key.length);
		output.write(iv);

		// read data from input into buffer, encrypt and write to output
		byte[] buffer = new byte[BUFFER_SIZE];
		int numRead;
		byte[] encrypted = null;
		while ((numRead = input.read(buffer)) > 0) {
			encrypted = encrypt.update(buffer, 0, numRead);
			if (encrypted != null) {
				output.write(encrypted);
			}
		}
		try { // finish encryption - do final block
			encrypted = encrypt.doFinal();
		} catch (IllegalBlockSizeException | BadPaddingException impossible) { }
		if (encrypted != null) {
			output.write(encrypted);
		}
	}

	/**
	 * Decrypts a stream of data that was encrypted by {@link #encrypt}.
	 * @param key
	 *   the key used to encrypt/decrypt the stream
	 * @param input
	 *   stream of encrypted data to be decrypted
	 * @param output
	 *   stream to which decrypted data will be written
	 * @return the key length for the decrypted stream (128, 192, or 256)
	 * @throws AES.InvalidAESStreamException
	 *   if the given input stream is not a valid AES-encrypted stream
	 * @throws AES.MismatchedKeyLengthException
	 *   if the given key not same size as used to encrypt the data
	 * @throws AES.StrongEncryptionNotAvailableException
	 *   if the stream is 192 or 256-bit encrypted, and the Java runtime's
	 *   jurisdiction policy files do not allow for AES-192 or 256
	 * @throws IOException
	 */
	public static int decrypt(byte[] key, InputStream input, OutputStream output)
			throws MismatchedKeyLengthException, InvalidAESStreamException, IOException,
			StrongEncryptionNotAvailableException {
		int keyBitLength = input.read() * 8;
		// Check validity of key length
		if (keyBitLength != 128 && keyBitLength != 192 && keyBitLength != 256) {
			throw new InvalidAESStreamException(keyBitLength);
		}
		if (keyBitLength != key.length * 8 ){
		    throw new MismatchedKeyLengthException();
		}
		
		// initialize AES decryption
		byte[] iv = new byte[16]; // 16-byte I.V. regardless of key size
		input.read(iv);
		Cipher decrypt = null;
		try {
			decrypt = Cipher.getInstance(CIPHER_SPEC);
			decrypt.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"), new IvParameterSpec(iv));
		} catch (NoSuchAlgorithmException | NoSuchPaddingException
				| InvalidAlgorithmParameterException impossible) { }
		  catch (InvalidKeyException e) { // 192 or 256-bit AES not available
			throw new StrongEncryptionNotAvailableException(keyBitLength, e);
		}
		
		// read data from input into buffer, decrypt and write to output
		byte[] buffer = new byte[BUFFER_SIZE];
		int numRead;
		byte[] decrypted;
		while ((numRead = input.read(buffer)) > 0) {
			decrypted = decrypt.update(buffer, 0, numRead);
			if (decrypted != null) {
				output.write(decrypted);
			}
		}
		try { // finish decryption - do final block
			decrypted = decrypt.doFinal();
		} catch (IllegalBlockSizeException | BadPaddingException e) {
			throw new InvalidAESStreamException(e);
		}
		if (decrypted != null) {
			output.write(decrypted);
		}

		return keyBitLength;
	}

	//******** EXCEPTIONS thrown by encrypt and decrypt ********

	/**
	 * Thrown if an attempt is made to encrypt a stream with an invalid AES key length.
	 */
	public static class InvalidKeyLengthException extends Exception {
		InvalidKeyLengthException(int length) {
			super("Invalid AES key length: " + length);
		}
	}

	/**
	 * Thrown if an attempt is made to decrypt a stream with a key length
	 * different from the key length used to encrypt.
	 */
	public static class MismatchedKeyLengthException extends Exception { }
	
	/**
	 * Thrown if 192- or 256-bit AES encryption or decryption is attempted,
	 * but not available on the particular Java platform.
	 */
	public static class StrongEncryptionNotAvailableException extends Exception {
		public StrongEncryptionNotAvailableException(int keySize) {
			super(keySize + "-bit AES encryption is not available on this Java platform.");
		}
		public StrongEncryptionNotAvailableException(int keySize, Exception e) {
			super(keySize + "-bit AES encryption is not available on this Java platform."+e.toString(), e);
		}
	}
	
	/**
	 * Thrown if an attempt is made to decrypt an invalid AES stream.
	 */
	public static class InvalidAESStreamException extends Exception {
		public InvalidAESStreamException() { super(); };
		public InvalidAESStreamException(int keySize) { super(""+keySize); };
		public InvalidAESStreamException(Exception e) { super(e); }
	}

}
