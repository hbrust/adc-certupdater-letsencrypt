![Docker Image CI](https://github.com/hbrust/adc-certupdater-letsencrypt/workflows/Docker%20Image%20CI/badge.svg?branch=master)

# adc-certupdater-letsencrypt

This project builds a docker container, which helps to use [Lets Encrypt Certificates](https://letsencrypt.org) on Citrix ADC.
I use this internally for automating our certificate management using dehydrated and push these certificates to Citrix ADC.

# Usage

At the moment `http-01` challenges are supported only. All configuration is done by configuration files. You can have multiple configuration files, one for each certificate you want to use.

## Configuration

There are two configuration files needed for a valid configuration.

1. The `.conf` file. See the `config-adc.example` files
2. A domains file referenced in the `.conf` file. This file contains all doamin names for the certificate (Subject Alternative Names) in one line divided by space. Any change in this files execute a renewal of the certificate.

The container tries in a intervall if 5 minutes to renew the certificates. A renewal will be exectuted if
* the certificates become invalid in the next 30 days
* there are configuration changes (e.g. domain changes)

You can pull it via Github Registry:

`docker pull ghcr.io/hbrust/adc-certupdater-letsencrypt:latest`

## Deployment

You need to provide mounts for
* `/config`: this directory is searched for `.conf` files and domain name files
* `/storage`: this is the directory where Dehydrated will store all ACME stuff (identities, certificates)

You can run it with the following command

```
docker create
        --name certupdater \
        -v "config_data:/config" \
        -v "cert_data:/storage"  \
        --restart unless-stopped \
        ghcr.io/hbrust/adc-certupdater-letsencrypt:latest
```

## Environment
At the moment there are no environment variables needed. It is planned for upcoming versions to add environment variables for configuration.

# Credits
This project is based on the work of [Ryan Butler](https://github.com/ryancbutler/ns-letsencrypt) and [Blog](https://www.techdrabble.com/citrix/18-letsencrypt-san-certificate-with-citrix-netscaler-take-2)
