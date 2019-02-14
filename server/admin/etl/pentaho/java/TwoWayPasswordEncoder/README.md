# Kettle Secure Password-Encoding Plugin

Java source defining a simple Kettle 'TwoWayPasswordEncoder' which securely encrypts DB connection passwords with FIPS 140-2 compliant encryption methods (AES-CBC with 256bit keys).
 * default "Encryption" method is just simple, reversible XOR of the supplied password (nonsecure).
    * [http://wiki.pentaho.com/display/EAI/Password+encoding+options](http://wiki.pentaho.com/display/EAI/Password+encoding+options) - *"... standard encoding or obfuscation system is obscure enough ... it doesn't use any specific passphrase or password to encode and decode the actual values"*
    * [https://github.com/pentaho/pentaho-kettle/blob/master/core/src/org/pentaho/di/core/encryption/KettleTwoWayPasswordEncoder.java#L34](https://github.com/pentaho/pentaho-kettle/blob/master/core/src/org/pentaho/di/core/encryption/KettleTwoWayPasswordEncoder.java#L34) - *"... basic encryption of passwords in Kettle. Note that it's not really encryption, it's more obfuscation"*
    * [http://wiki.pentaho.com/display/EAI/PDI+Two-Way+Password+Encoding+plugins](http://wiki.pentaho.com/display/EAI/PDI+Two-Way+Password+Encoding+plugins) - *"version 5.1 of the Kettle API you can create your own plugin to do password encoding"*

## Overview
 * [Installation](#installation)
 * [Usage](#usage)
 * [Building](#building)
 * [Testing](#testing)

## Installation

1. Navigate to folder
 ```
C:\Pentaho\data-integration\plugins\
 ```

2. Copy 'kettle-aes-password-plugin.jar' to the Pentaho Data-Integration folder above.
 * download link: [kettle-aes-password-plugin.jar](server/admin/etl/pentaho/jars/plugins/kettle-aes-password-plugin/kettle-aes-password-plugin.jar)

3. Open your kettle.properties config file:
 ```
notepad C:\Users\nameof.youruseraccount\.kettle\kettle.properties
 ```

4. Add the following 2x lines:
 ```
KETTLE_PASSWORD_ENCODER_PLUGIN = Aes256_Encrypted
KETTLE_PASSWORD_ENCODER_KEY = ##SECRET KEY GOES HERE##
 ```
 * Generate the teams shared, symmetric encryption key. With Openssl, [run command](http://www.ibm.com/support/knowledgecenter/SSLVY3_9.7.0/com.ibm.einstall.doc/topics/t_einstall_GenerateAESkey.html):
        ```
        openssl enc -aes-256-cbc -k unimportantSeedValue657 -md sha1 -P
        ```
 * Output will look something like:

    ```
salt=A1F1DC376E1DD0CF
key=DB113F9E0F6E56BCE7333BEDED147422467792E74F3C462B5782CA30C7C2E038
iv =409265EC61F86AF1D58654B586C3196D
    ```
 * Copy only the value for 'key=' into your kettle.properties as "KETTLE_PASSWORD_ENCODER_KEY =", and securely share the key with teammembers.

5. Download Java Cryptography Extension (JCE) unlimited encryption policy files for Java 8 (_Unlimited Strength Jurisdiction Policy Files 8_) from Oracle
 * [http://www.oracle.com/technetwork/java/javase/downloads/jce8-download-2133166.html](http://www.oracle.com/technetwork/java/javase/downloads/jce8-download-2133166.html)
 1. Extract the 'jce_policy-8.zip' to a temporary folder
    * !!! _*if you skip Extracting the files & try to just open .zip to drag/drop Windows 7 permissions may not permit you to paste the files to destination folder (no error message, files just never show up). If you extract first, then drag/drop the copy will definitely work correctly.*_ !!!

6. Identify the 64-bit Java install that is used to run Pentaho tools:
 ```
# Check environmental variable %PENTAHO_JAVA_HOME%
# or, if not configured run:
c:\> java.exe -version
# Navigate to Java version indicated by above command, if final line says "64-bit VM" the java will be in C:\Program Files\
 ```

6. Open the "lib\security" subfolder:
 ```
C:\Program Files\Java\jdk1.8.0_102\jre\lib\security
 ```

7. Rename both of the current Policy files:

    ```
US_export_policy.jar ---(rename to)--->  US_export_policy.jar.Limited
local_policy.jar     ---(rename to)--->  local_policy.jar.Limited
    ```
 * _*A priviledged (system-administrator) login may be needed to rename these files*_

8. Copy all three Unlimited Strength policy files into the "lib\security" folder

    ```
US_export_policy.jar
local_policy.jar
README.txt
    ```
 * _*A priviledged (system-administrator) login may be needed to add these new files*_

9. Shutdown & restart Pentaho tools

## Usage
Plugin installation can be confirmed by opening the Spoon program and navigating to:
```
Tools > Show plugin information
Select category 'TwoWayPasswordEncoder'
Check that the #1 TwoWayPasswordEncoder entry has "Aes256_Encrypted" in the 'ID' column
```
If ID is not shown as #1 entry, see [Installation](#install)
### Encrypting passwords in new files
The installed plugin is used automatically once configured. Simply configure connections & click save as usual.
 * Correct password encryption can verified by viewing file XML manually and confirming that default (insecure) *"<password>Encrypted ..."* encoding flags have all been replaced with FIPS 140-2 compliant indicator: *"<password>Aes256_Encrypted ..."*

### Encryping existing files
To encrypt passwords in existing .KTR/.KJB files, open the file, retype the password and save.
 * Resaving an existing (insecure) file, without retyping password, will still AES256 encrypt the credential. However, the credential will be double-encoded (original insecure-encoding, wrapped by the secure-encoding) and will not be useable by pentaho tools, until the credential password is explicitly re-entered & saved.

### Encrypting new passwords for use in kettle.properties
To encrypt a password for use as [a ``kettle.properties`` variable](database/migration#database-connection-configuration):
  1. Create a new Pentaho Transformation via Spoon & confirm AES plugin installed [per Usage documentation](#usage)
    ```
Tools > Show plugin information ... > TwoWayPasswordEncoder
    ```
  2. Via Spoon Design > Scripting side panel add ``Execute SQL Script`` to transformation, double-click step to edit, then click _New ..._ to configure a Database connection with the new password.
  3. Click 'test' to confirm new password typed correctly
  4. Save transformation
  5. Navigate to folder with transformation .KTR from Step 4. & open .KTR file with any text editor (Notepad, Notepad++, gedit, etc.)
  6. Search file for <password> key & copy the entire password value
     * _the entire password value will start with: Aes256_Encrypted followed by jumbled characters_
  7. Via Spoon Edit > edit kettle.properties menu paste entire value into kettle.properties file (or Python [pentaho template file](server/admin/etl/pentaho/kettle.properties_ConnectionDetails) via your text editor)
    ```
# Example:
db.etl.dw.password=Aes256_EncryptedIHnAZIJCMZ1Ed1QOcb4GGgX&#x2F;ED0dD62q9YkMlYqPFRPd
    ```
  8. Convert any XML encoded characters, back into their ASCII representation
    * e.g.: '&#x2F;' above, is an XML encoding for a '/' character in the encrypted password
    ```
# Example:
db.etl.dw.password=Aes256_EncryptedIHnAZIJCMZ1Ed1QOcb4GGgX/ED0dD62q9YkMlYqPFRPd
    ```
  9. Open your test Transformation database connection and paste the new properties variable in to the field for password value
    ```
  ${db.etl.dw.password}
    ```
  10. Test connection, to confirm new kettle.properties password value works

## Building

### Prerequisites
 * A Java-8 JDK _(I used the 'openjdk-8-jdk' Debian package)_
 * JCE unlimited strength Cryptographic Extensions

1. Unpack Pentaho Data-Integration .zip archive
 ```
unzip ../pdi-ce-6.1.0.1-196.zip -d /tmp/warehouse-pentaho-di/
 ```

2. Compile Java source
 ```
mkdir /tmp/warehouse-pentaho-build
javac -d /tmp/warehouse-pentaho-build -cp /tmp/warehouse-pentaho-di/lib/kettle-core-*.jar Aes256EncoderPlugin.java AES.java
 ```

3. Pack class files into kettle-aes-password-plugin.jar.jar
 ```
mkdir -p /tmp/warehouse-pentaho-build/gov/noaa/nwfsc/pentaho/encryption
cd /tmp/warehouse-pentaho-build
jar cf kettle-aes-password-plugin.jar gov
 ```

## Testing

### Prerequisites
 * JUnit 4 .jars (https://github.com/junit-team/junit4/wiki/Download-and-Install)
 * kettle-aes-password-plugin.jar ([see: Building](#building))

1. Compile test source
 ```
javac -cp /tmp/warehouse-pentaho-build/kettle-aes-password-plugin.jar:junit-4.12.jar AESTest.java
 ```

2. Run tests
 ```
java -cp .:/tmp/warehouse-pentaho-build/kettle-aes-password-plugin.jar:junit-4.12.jar:hamcrest-core-1.3.jar org.junit.runner.JUnitCore AESTest
 ```