# Ordering a Subnet
Request a subnet from: https://intel.service-now.com/aem?id=aem_sc_cat_item&sys_id=4854e184f8bd08105c3c3e46d73919bc
Required information is: 
1. Business need 
1. Size of the subnet (from drop down menu, better ask for /29 -> 6 usable IP addresses)
1. Business unit
1. Owner

![image](https://github.com/intel-innersource/applications.manufacturing.intel.fab-data-analytics.iris2/assets/65765689/b8374bcd-2a17-426d-a3dc-3d623c476441)

![image](https://github.com/intel-innersource/applications.manufacturing.intel.fab-data-analytics.iris2/assets/65765689/8a390907-7953-4eb4-8b4b-c98dabfe2145)

# Request to open some ports
Since it is a restricted subnet the firewall is blocking the connection such as the DB, and file shared port. 
Follow the instructions below:

* PPF spreadsheets must be filled out with new flows in red. Please follow the instructions in the template. **Missing information will cause a delay or cancellation of your request**. (See sample below) Please use the link: https://goto.intel.com/firewalltemplate

* Please list every firewall port you expect is needed, in our case we added: 
   * 445 is the SMB file share port
   * 5433 is the DB port
   * Please try and include any other ports that will be needed

![image](https://github.com/intel-innersource/applications.manufacturing.intel.fab-data-analytics.iris2/assets/65765689/e0c0f8af-ea27-483d-b615-e8436f05945a)

* To allow the connection, please open a firewall request https://intel.service-now.com/aem?id=aem_sc_cat_item&sys_id=62004d312073f3005c3cb313dd872e44
* Fill out the PPF template and attach it to your request.

![MicrosoftTeams-image (55)](https://github.com/intel-innersource/applications.manufacturing.intel.fab-data-analytics.iris2/assets/65765689/d3285dd6-0bf4-429a-8ba6-5406edfeb6d4)

![MicrosoftTeams-image (56)](https://github.com/intel-innersource/applications.manufacturing.intel.fab-data-analytics.iris2/assets/65765689/a46371a7-db57-4a1e-9bb0-94e792688b57)

![MicrosoftTeams-image (57)](https://github.com/intel-innersource/applications.manufacturing.intel.fab-data-analytics.iris2/assets/65765689/15407c70-f077-41db-8532-dfacf1483d73)




