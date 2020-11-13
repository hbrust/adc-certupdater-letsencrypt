FROM debian:stable
Maintainer Helge Brust <helge@labbifant.de>

# install git
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends -y ca-certificates python3 python3-requests git openssl curl

# clone dehydrated
RUN git clone https://github.com/dehydrated-io/dehydrated.git /opt/dehydrated && \
    mkdir -p /var/www/dehydrated && \
    mkdir -p /config && \
    mkdir -p /storage

# copy ADC hooks
COPY ["citrix-adc_hooks.py", "config-adc.example", "/opt/adc-hook/"]

# copy CMD script
COPY letsencrypt-start.sh /

CMD ./letsencrypt-start.sh
