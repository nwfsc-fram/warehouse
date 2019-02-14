# Environment architecture 

This covers where in the organization the different components sit and how they communicate and interact. Architecture also impacts access to the system from other parts of the organization and/or the general public.

### Summary
Warehoused FRAM data resides on the EnterpriseDB ‘dwprod’ database. FRAM Data Warehouse Service is installed on a second, internal NWFSC web server. A third, reverse proxy server at NWFSC implements TLS transport encryption, accepts secure HTTP requests from the General public; forwarding them to the NWFSC FRAM Data Warehouse web server. FRAM Data Warehouse web server at NWFSC maintains a whitelist of known NWFSC proxies, querying dwprod database on-demand upon request receipt. The fixed-format, non-confidential, summary information from database is then transformed by Data Warehouse web service into requested file type and transmitted back to requesting user via NWFSC HTTP proxy server. Requests from password-authorized users for confidential data, received from known NWFSC proxies, query dwprod database using user list of per-project NDAs, role based access controls, and dedicated connection for sensitive data.

# Application architecture

This covers different components of the application and where they sit in the environment architecture and how they communicate and interact within the application.

### Summary
Continuum Analytics Python runtime (similar to MicroSoft .NET runtime) is installed as a user program, in a single directory owned by the Apache webserver’s OS-level service account; Data Warehouse service program files reside in a single directory, owned by the Apache webserver’s OS-level service account;  Via startup script the OS runs the Apache webserver program as the webserver’s OS-level service account.  EnterpriseDB Postgres Advanced Server is installed on a second, internal NWFSC server with local firewall; TCP port is opened on the database server firewall to enable intranet connection from the Data Warehouse application.