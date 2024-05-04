# Configuration - oneM2M Resources

The configuration file contains settings for the default values or configurable behaviour of oneM2M resources. These settings are used when creating resources and, if allowed, can be overridden by the values in the request.

## ACP

**Section: `[resource.acp]`**

The default values for Access Control Policies (ACP) resources.

| Setting        | Description                                                                                                           |Default | Configuration Name            |
|:---------------|:----------------------------------------------------------------------------------------------------------------------|:-------|:------------------------------|
| selfPermission | Default selfPermission when creating an ACP resource. This is the decimal representation of the permissions bitfield. | 51     | resource.acp.selfPermission   |


## Action

**Section: `[resource.actr]`**

The default values for Action resources.

| Setting       | Description                                                                                                | Default                | Configuration Name          |
|:--------------|:-----------------------------------------------------------------------------------------------------------|:-----------------------|:----------------------------|
| ecpContinuous | Default for the *evalControlParam* attribute, when the *evalMode* is `continuous`. The unit is number.     | 1.000                  | resource.actr.ecpContinuous |
| ecpPeriodic   | Default for the *evalControlParam* attribute, when the *evalMode* is `periodic`. The unit is milliseconds. | 10.000 ms = 10 seconds | resource.actr.ecpPeriodic   |


## Container

**Section: `[resource.cnt]`**

The default values for Container resources.

| Setting      | Description                        | Default      | Configuration Name        |
|:-------------|:-----------------------------------|:-------------|:--------------------------|
| enableLimits | Enable/disable the default limits. | False        | resource.cnt.enableLimits |
| mni          | Default for maxNrOfInstances.      | 10           | resource.cnt.mni          |
| mbs          | Default for maxByteSize.           | 10.000 bytes | resource.cnt.mbs          |


## Group

**Section: `[resource.grp]`**

The default values for Group resources.

| Setting              | Description                                                                                                                                                                                                  |Default | Configuration Name                |
|:---------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:-------|:----------------------------------|
| resultExpirationTime | Set the time for aggregating the results of a group request before interrupting. This is the CSE default and can be overwritten by a request. The format is the time in ms. A value of 0 ms means no timeout.| 0 ms   | resource.grp.resultExpirationTime |


## LocationPolicy

**Section: `[resource.lcp]`**

The default values for the Container of a LocationPolicy resources.

| Setting | Description                                                       |Default      | Configuration Name |
|:--------|:------------------------------------------------------------------|:------------|:-------------------|
| mni     | Default for maxNrOfInstances for the LocationPolicy's container.  | 10          | resource.lcp.mni   |
| mbs     | Default for maxByteSize for the LocationPolicy's container.	      | 10.000 bytes| resource.lcp.mbs   |


## Request

**Section: `[resource.req]`**

The default values for Request resources.

| Setting        | Description                                                        |Default     | Configuration Name |
|:---------------|:-------------------------------------------------------------------|:-----------|:-------------------|
| expirationTime | A &lt;request> resource's  expiration time in seconds. Must be >0. | 60 seconds | resource.req.et    |


## Subscription

**Section: `[resource.sub]`**

The default values for Subscription resources.

| Setting             | Description                                                                           | Default | Configuration Name                 |
|:--------------------|:--------------------------------------------------------------------------------------|:--------|:-----------------------------------|
| batchNotifyDuration | Default for the batchNotify/duration in seconds. Must be >0.                          | 60 sec  | resource.sub.batchNotifyDuration   |

## TimeSeries

**Section: `[resource.ts]`**

The default values for TimeSeries resources.

| Setting      | Description                        | Default      | Configuration Name       |
|:-------------|:-----------------------------------|:-------------|:-------------------------|
| enableLimits | Enable/disable the default limits. | False        | resource.ts.enableLimits |
| mni          | Default for maxNrOfInstances.      | 10           | resource.ts.mni          |
| mbs          | Default for maxByteSize.           | 10.000 bytes | resource.ts.mbs          |
| mdn          | Default for missingDataMaxNr.      | 10           | resource.ts.mdn          |


## TimeSyncBeacon

**Section: `[resource.tsb]`**

The default values for TimeSyncBeacon resources.

| Setting | Description                                                                                                                                                    | Default         | Configuration Name |
|:--------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------|:----------------|:-------------------|
| bcni    | Default timeSyncBeacon interval. This is the duration between to beacon notifications sent by the CSE to an AE or CSE.T he format must be an ISO8601 duration. | "PT1H" = 1 hour | resource.tsb.bcni  |
| bcnt    | Default timeSyncBeacon threshold. When this time threshold is passed then a beacon notifications is sent to an AE or CSE.                                      | 10 seconds      | resource.ts.bcnt   |

