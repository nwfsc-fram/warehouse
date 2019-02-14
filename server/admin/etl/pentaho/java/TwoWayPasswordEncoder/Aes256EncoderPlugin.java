// -*- indent-tabs-mode:t; -*-
/** Java source file implementing a Pentaho TwoWayPasswordEncoder secured
 * via AES encryption
 *
 * Copyright (C) 2016 ERT Inc. */
package gov.noaa.nwfsc.pentaho.encryption;

import java.util.List;
import java.util.ArrayList;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.ByteArrayInputStream;
import java.io.UnsupportedEncodingException;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import java.lang.NullPointerException;
import java.lang.IllegalArgumentException;
import java.lang.SecurityException;
import java.util.Base64;
import javax.xml.bind.DatatypeConverter;

import org.pentaho.di.core.encryption.TwoWayPasswordEncoderPlugin;
import org.pentaho.di.core.encryption.TwoWayPasswordEncoderInterface;

import org.pentaho.di.core.exception.KettleException;
import org.pentaho.di.core.util.StringUtil;

import gov.noaa.nwfsc.pentaho.encryption.AES;
import gov.noaa.nwfsc.pentaho.encryption.AES.InvalidKeyLengthException;
import gov.noaa.nwfsc.pentaho.encryption.AES.StrongEncryptionNotAvailableException;
import gov.noaa.nwfsc.pentaho.encryption.AES.MismatchedKeyLengthException;
import gov.noaa.nwfsc.pentaho.encryption.AES.InvalidAESStreamException;

/** Simple utility class, defining constants for use in Aes256EncoderPlugin
 */
class Aes256EncoderPrefixUtil {
	/** String used as plugin ID & put in front of pw to indicate encryption*/
	public static final String id = "Aes256_Encrypted";

	/** String used as plugin Title in user-interface dialogs */
	public static final String title = "AES Password Encoder";

	/** String, defining kettle.property attribute containing encryption KEY*/
	public static final String key_variable = "KETTLE_PASSWORD_ENCODER_KEY";
}

/** AES_256 TwoWayPasswordEncoder
 * per: https://github.com/pentaho/pentaho-kettle/blob/master/core/src/org/pentaho/di/core/encryption/KettleTwoWayPasswordEncoder.java
 */
@TwoWayPasswordEncoderPlugin(
	id = Aes256EncoderPrefixUtil.id
	, name = Aes256EncoderPrefixUtil.title
)
public class Aes256EncoderPlugin implements TwoWayPasswordEncoderInterface {
	/** String that is put in front of the password to indicate encryption*/
	public static final String PASSWORD_ENCRYPTED_PREFIX = Aes256EncoderPrefixUtil.id;

	/** Byte array, representing the kettle.properies secret key*/
	private byte[] key = null;

	public Aes256EncoderPlugin() {
	}

	@Override
	public void init() throws KettleException {
		try {
			key = getKey();
		} catch (EncoderKeyNotFoundException e) {
			throw new KettleException(e);
		}
		
		// inspect key
		if (key.length * 8 != 256) {
			Exception e = new UnsupportedKeyLengthException(key.length * 8);
			throw new KettleException(e);
		}
		// test key
		try {
			ByteArrayOutputStream outputByteBuffer = encrypt("test");
		} catch (InvalidKeyLengthException | StrongEncryptionNotAvailableException | IOException e) {
			throw new KettleException(e);
		}
	}

	@Override
	public String[] getPrefixes(){
		return new String[] {PASSWORD_ENCRYPTED_PREFIX};
	}

	@Override
	public String encode(String rawPassword){
		boolean includePrefix = true;
		return encode(rawPassword, includePrefix);
	}

	@Override
	public String encode(String rawPassword, boolean includePrefix){
		if (includePrefix) {
			return encryptPasswordIfNotUsingVariables(rawPassword);
		} else {
			return encryptPassword(rawPassword);
		}
	}

	@Override
	public String decode(String encodedPassword){
		if (hasOurPrefix(encodedPassword) ){
			encodedPassword = removeOurPrefix(encodedPassword);
		}
		return decryptPassword(encodedPassword);
	}

	@Override
	public String decode(String encodedPassword, boolean optionallyEncrypted){
		if (encodedPassword == null){
			return null;
		}
		if (optionallyEncrypted){
			if (hasOurPrefix(encodedPassword) ){
				encodedPassword = removeOurPrefix(encodedPassword);
				return decryptPassword(encodedPassword);
			} else {
				return encodedPassword; //Nothing we can do, just pass it on
			}
		} else {
			return decryptPassword(encodedPassword);
		}
	}

	private boolean hasOurPrefix(String encodedPassword){
		boolean trueOrFalse = (encodedPassword != null && encodedPassword.startsWith(PASSWORD_ENCRYPTED_PREFIX));
		return trueOrFalse;
	}

	private String removeOurPrefix(String encodedPassword){
		int prefixLength = PASSWORD_ENCRYPTED_PREFIX.length();
		return encodedPassword.substring(prefixLength);
	}

	public final String encryptPassword(String password) {
		if (password == null){
			return "";
		}
		if (password.length() == 0){
			return "";
		}

		ByteArrayOutputStream outputByteBuffer = null;
		try {
			outputByteBuffer = encrypt(password);
		} catch (InvalidKeyLengthException | StrongEncryptionNotAvailableException | IOException e) {
			// Never will happen, init() has pre-checked the key
			assert false;
		}
		String ciphertext = decodeByteBuffer(outputByteBuffer);
		return ciphertext;
	}

	public final String decryptPassword(String encryptedPassword){
		if (encryptedPassword == null){
			return "";
		}
		if (encryptedPassword.length() == 0){
			return "";
		}

		byte[] encryptedBytes = Base64.getDecoder().decode(encryptedPassword);
		ByteArrayInputStream encryptedInputBuffer = new ByteArrayInputStream(encryptedBytes);
		ByteArrayOutputStream outputByteBuffer = new ByteArrayOutputStream();
		try {
			AES.decrypt(key, encryptedInputBuffer, outputByteBuffer);
		} catch (StrongEncryptionNotAvailableException e) {
			// Will never happen, init() has pre-checked the key
			assert false;
		} catch (MismatchedKeyLengthException | InvalidAESStreamException | IOException e) {
        	assert false; //Failure, no way to recover
        }
        String plaintext = null;
		try {
			plaintext = outputByteBuffer.toString("UTF-8");
		} catch (UnsupportedEncodingException e) {
			assert false; //Failure, no way to recover!
		}
		return plaintext;
	}

	public final String decodeByteBuffer(ByteArrayOutputStream outputByteBuffer){
		byte[] bytes = outputByteBuffer.toByteArray();
		return Base64.getEncoder().encodeToString(bytes);
	}

	public final ByteArrayOutputStream encrypt(String password) throws
			UnsupportedPasswordEncodingException, InvalidKeyLengthException, StrongEncryptionNotAvailableException, IOException {
		byte[] plaintextBytes = {};
		try {
			 plaintextBytes = password.getBytes("UTF-8");
		} catch (UnsupportedEncodingException e) {
			throw new UnsupportedPasswordEncodingException(e);
		}
		ByteArrayInputStream unencryptedInputBuffer = new ByteArrayInputStream(plaintextBytes);
		ByteArrayOutputStream outputByteBuffer = new ByteArrayOutputStream();
		AES.encrypt(key, unencryptedInputBuffer, outputByteBuffer);
		return outputByteBuffer;
	}

	public final String encryptPasswordIfNotUsingVariables(String password){
		String encryptedPassword = "";
		List<String> listOfVariables = new ArrayList<String>();
		StringUtil.getUsedVariables(password, listOfVariables, true );
		if (listOfVariables.isEmpty() ) {
		  encryptedPassword = PASSWORD_ENCRYPTED_PREFIX + encryptPassword(password);
		} else {
		  encryptedPassword = password;
		}

		return encryptedPassword;
	}

	public static final byte[] getKey() throws EncoderKeyNotFoundException {
		String keyString = null;
		try {
			keyString = System.getProperty(Aes256EncoderPrefixUtil.key_variable);
		} catch ( NullPointerException | IllegalArgumentException
				| SecurityException e){
			throw new EncoderKeyNotFoundException();
		}
		byte[] key = DatatypeConverter.parseHexBinary(keyString);
        return key;
	}

	/** Thrown if kettle.properties has not been configured with KEY */
	public static class EncoderKeyNotFoundException extends Exception{
		EncoderKeyNotFoundException(){
			super("kettle.properties "+Aes256EncoderPrefixUtil.key_variable+" not set");
		}
	}
	/** Thrown if kettle.properties KEY is incorrectly sized */
	public static class UnsupportedKeyLengthException extends Exception{
		UnsupportedKeyLengthException(int keyBitLength){
			super( "kettle.properties "+Aes256EncoderPrefixUtil.key_variable
		          +" length must be 256bits. Invalid length: "+keyBitLength
		          +"bits");
		}
	}
	/** Thrown if kettle.properties KEY malformed */
	public static class UnsupportedPasswordEncodingException extends UnsupportedEncodingException{
		UnsupportedPasswordEncodingException(Exception e){
			super("Unsupported password encoding: "+e.getLocalizedMessage());
		}
	}
}
