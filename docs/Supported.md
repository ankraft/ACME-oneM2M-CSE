# Supported Resource Types and Functionalities

## Resources

The CSE supports the following oneM2M resource types:

- **CSEBase (CB)**
- **Access Control Policy (ACP)**
- **Remote CSE (CSR)**  
Announced resources are yet not supported. Transit request, though, to resources on the remote CSE are supported.
- **Application Entity (AE)**
- **Container (CNT)**
- **Content Instance (CIN)**
- **Subscription (SUB)**  
Notifications via http to a direct url or an AE's Point-of-Access (POA) are supported as well.
- **Group (GRP)**  
The support includes requests via the *fopt* (fan-out-point) virtual resource.
- **Node (NOD)**  
The support includes the following **Management Object (mgmtObj)** specializations:
	- **Firmware (FWR)**
	- **Software (SWR)**
	- **Memory (MEM)**
	- **AreaNwkInfo (ANI)**
	- **AreaNwkDeviceInfo (ANDI)**
	- **Battery (BAT)**
	- **DeviceInfo (DVI)**
	- **DeviceCapability (DVC)**
	- **Reboot (REB)**
	- **EventLog (EVL)**
- **FlexContainer Specializations**  
Any specializations is supported. There is no check performed against a schema (e.g. via the *cnd* attribute).

Resources of any other type are stored in the CSE but no further processed and no checks are performed on these resources. The type is marked as *unknown*.

## Discovery
The following result contents are implemented for Discovery:

- attributes + child-resources (rcn=4)
- attributes + child-resource-references (rcn=5)
- child-resource-references (rcn=6)
- child-resources (rcn=8)

# Limitations
- **This is by no means a fully compliant, secure or stable CSE! Don't use it in production.**
- This CSE is intended for educational purposes. The underlying database system is not optimized in any way for high-volume, high-accessibility.
- No support for https yet.
- Security: None. Please contact me if you have suggestions to improve this.
- Unsupported resource types are just stored, but no check or functionality is provided for those resources. The same is true for unknown resource attributes. Only a few attributes are validated.
