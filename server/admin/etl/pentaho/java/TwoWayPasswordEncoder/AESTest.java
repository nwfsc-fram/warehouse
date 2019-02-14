// -*- indent-tabs-mode:t; -*-
import java.io.ByteArrayInputStream;
import java.io.UnsupportedEncodingException;
import java.io.IOException;
import java.io.ByteArrayOutputStream;
import javax.xml.bind.DatatypeConverter;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import org.junit.Test;

import gov.noaa.nwfsc.pentaho.encryption.AES;
import gov.noaa.nwfsc.pentaho.encryption.AES.InvalidKeyLengthException;
import gov.noaa.nwfsc.pentaho.encryption.AES.StrongEncryptionNotAvailableException;
import gov.noaa.nwfsc.pentaho.encryption.AES.MismatchedKeyLengthException;
import gov.noaa.nwfsc.pentaho.encryption.AES.InvalidAESStreamException;

public class AESTest {
    @Test
    public void encrypt() {
    	String secret = "Mary had a little lamb.";
    	/* Test, with a particularly weak (easily typed) key */
    	String badKeyHexString = "0100FACE0100CAFE01000100010001000"
    							+ "1000100010001000100010001000100";
    	byte[] bad_key = DatatypeConverter.parseHexBinary(badKeyHexString);
      	// Feed data into the encrypt method
        ByteArrayOutputStream encryptedOutputBuffer = new ByteArrayOutputStream();
      	byte[] testInputBytes = {};
        try {
        	 testInputBytes = secret.getBytes("UTF-8");
        } catch (UnsupportedEncodingException e) {
        	assertNull(e); // Should never get here
        }
        ByteArrayInputStream testInputBuffer = new ByteArrayInputStream(testInputBytes);
        try {
        	// Test: part 1 of 2
	        new AES().encrypt(bad_key, testInputBuffer, encryptedOutputBuffer);
        } catch ( InvalidKeyLengthException
        		 | StrongEncryptionNotAvailableException
        		 | IOException e) {
        	assertNull(e); // Should never get here
    	}
    	byte[] encryptedBytes = encryptedOutputBuffer.toByteArray();

    	// Feed data into decrypt method
        ByteArrayInputStream encryptedInputBuffer = new ByteArrayInputStream(encryptedBytes);
        ByteArrayOutputStream decryptionOutputBuffer = new ByteArrayOutputStream();
        try {
        	// Test: part 2 of 2
	        new AES().decrypt(bad_key, encryptedInputBuffer, decryptionOutputBuffer);
        } catch ( MismatchedKeyLengthException
        		 | StrongEncryptionNotAvailableException
        		 | InvalidAESStreamException
        		 | IOException e) {
        	assertNull(e); // Should never get here
    	}

    	// Finally: Check the output!
        try {
        	 assertEquals(secret, decryptionOutputBuffer.toString("UTF-8"));
        } catch (UnsupportedEncodingException e) {
        	assertNull(e); // Should never get here
        }
    }
}
