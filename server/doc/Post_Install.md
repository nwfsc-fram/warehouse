# FRAM Data Warehouse web service - Post Install checklist

2016-JUN-07

Checklist to be completed after installation of Data Warehouse product.

## Checklist prerequisites
* [ ] 1) A computer connected to a non-NOAA LAN/non-VPN internet connection. *(e.g.: telephone connected to carriers network, GF PC connected to NWFSC-Guest WiFi with VPN turned off)*
    * This ensures checklist reviews what external/public warehouse users have access to.

## Post Install checklist
* [ ] 1) Basic data warehouse query - by species, by time filter, by layer
    * direct browser to https://www.nwfsc.noaa.gov/data
        * __Expected outcome:__ Browser redirects to https://www.nwfsc.noaa.gov/data/map & mapping interface is shown
    * enter <u>bocaccio</u> into species Search Filter & click matching name in dropdown.
        * __Expected outcome:__ interface shows list of matching species & creates a chit when clicked
    * check "Trawl Survey > Catch" layer.
        * __Expected outcome1:__ map load indicator spins & bocaccio catches are plotted on map off US west coast
        * __Expected outcome2:__ 'Trawl Catch' label & data rows are shown below horizontal separator
* [ ] 2) ArcGIS layers are active
    * check "Acoustics / Hake Survey > NASC 2012" layer.
        * __Expected outcome:__ acoustic transects plot on map off BC & US west coasts
* [ ] 3) Basic map navigation works
    * move map right/left, zoom in & zoom out.
* [ ] 4) Basic buttons work
    * click Citations, Contact buttons.
        * __Expected outcome:__ Citations popover & Contacts popovers display
    * click data table 'CSV' button
        * __Expected outcome:__ browser downloads a .CSV file of Trawl Catch data
