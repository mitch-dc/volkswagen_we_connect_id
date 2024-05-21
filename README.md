# Volkswagen We Connect ID [ONLY FOR EUROPE]
_Volkswagen We Connect ID sensor provides statistics from the Volkswagen ID Api thru [WeConnect-python lib](https://pypi.org/project/weconnect/)._

**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Show information from your Volkswagen ID car.
`button` | Start climatization in your Volkswagen ID car.

![image](https://user-images.githubusercontent.com/15835274/149675681-a0c6804c-3179-4fd3-ad74-ab489c8986dd.png)


## Installation

### HACS
The easiest way to add the component to your Home Assistant installation is
using [HACS](https://hacs.xyz). Add this GitHub repository as a [custom
repository](https://hacs.xyz/docs/faq/custom_repositories), then follow the
instructions under [Configuration](#configuration) below.

### Manual

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `volkswagen_we_connect_id`.
4. Download _all_ the files from the `custom_components/volkswagen_we_connect_id/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Follow the instructions under [Configuration](#configuration) below.

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/volkswagen_we_connect_id/__init__.py
custom_components/volkswagen_we_connect_id/manifest.json
custom_components/volkswagen_we_connect_id/sensor.py
.. etc
```

##  Configuration 

It's important that you first use the app, connect the app to the car and use it at least once. 
After that enable the integration on the integration page in Home Assistant with your e-mail and password that you use to login into the app. Wait a couple of seconds and 1 or more devices (your cars) with entities will show up. 

## Tested Cars
_This integration only works with cars sold in Europe and use the WeConnect ID app_

* Volkswagen ID.3
* Volkswagen ID.4
* Volkswagen ID.5
* Volkswagen ID Buzz
* Volkswagen Tiguan (MKII)

## Requirements

Home Assistant Core *2023.3.1* or higher

