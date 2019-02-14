# FRAM Data Warehouse web service - Code Verification

2017-APR-25

Code verification process for review of *FRAM Data Warehouse web service* code updates, prior to release.  
Verification of code update is not complete until a final check status of 'YES', with all accompanying details, is obtained for every checklist item.

## Code review personnel

Code review must be completed by a minimum of one individual authorized to publish publically accessable information to the *FRAM Data Warehouse web service*.

### Authorized staff
* __TBD__ - *for details, see Todd Hay.*

### Training
Before completing code review, above authorized staff must have completed (__TBD__ - *for details, see Todd Hay.*) NWFSC training to correctly identify information as nonpublic.

## Checklist

Answer 'YES' or 'NO' for each item:

1. [ ] Is the proposed method and implementation of input validation sufficient to protect the integrity of the system, and its data, from unauthorized access or modification?
2. [ ] Has proposed update been committed to version control? Version control repository location: _________________, Commit number of proposed update: _________________________
3. [ ] Has the proposed update been included in the project requirements documentation? ([URL: project requirements](Requirements.md))
4. [ ] Are automated tests (Unit, Integration) as well as updates to the Test Plan provided, that demonstrate the correct functioning of proposed update? ([URL: Test Plan](TESTING.md))
4. [ ] Did automated tests included checks for Python modules with known vulnerabilities? Jenkins build #: ______
5. [ ] Were all automated tests run, and did the proposed update pass all tests?
6. [ ] Have all Test Plan test cases been completed successfully with the proposed update?
97. [ ] Review proposed publicly accessible Service content for nonpublic information. 
98. [ ] Has review of the publicly accessible Service for nonpublic information been conducted in the last year? Date of last review: _________________
99. [ ] Has all discovered, nonpublic information been removed from the publicly accessible Service.
100. [ ] Record SHA256 checksum of the deploy package, produced from the reviewed source code. SHA256 Checksum: _____________________________________________________
101. [ ] Has proposed update been scanned for network security and system vulnerabilities, and all Category I and II findings been mitigated? Scan results file: __________________________, Date and time of scan: ________________________________

## Sources
[Python Security Project](https://github.com/ebranca/owasp-pysec/wiki)  
[OWASP Secure Coding Practices](https://www.owasp.org/index.php/OWASP_Secure_Coding_Practices_-_Quick_Reference_Guide)  
[edX Python coding guildlines](https://web-beta.archive.org/web/20150329163922/https://github.com/edx/edx-platform/wiki/Python-Guidelines)  
[Best practices adopted by edX Python E-learning portal](https://github.com/edx/edx-lint/blob/master/pylintrc)  
[SQLAlchemy Connection Pooling](http://docs.sqlalchemy.org/en/latest/core/pooling.html)  
[Psycopg2 - Avoiding SQL injection](http://initd.org/psycopg/docs/usage.html#the-problem-with-the-query-parameters)  
[Psycopg2 - PostgreSQL best practices](http://pythonhosted.org/psycopg2/faq.html#best-practices)  
[OPM SDLC Policy and Standards](https://www.opm.gov/about-us/our-people-organization/support-functions/cio/opm-system-development-life-cycle-policy-and-standards.pdf)  
[Rules of Extreme Programming](http://www.extremeprogramming.org/rules.html)  
[NWFSC Developer Security Guidelines and Assessment](https://inside.nwfsc.noaa.gov/webapps/comtrack/resources/NOAA4600_DSGA_v3.9_[AppName]5.docx)