FROM debian:stable
Maintainer Helge Brust <helge@labbifant.de>
ARG DEHYDRATED_VER="0.7.0"

# install tools
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install --no-install-recommends -y ca-certificates wget python3 python3-requests git openssl curl

# get dehydrated from release
RUN wget https://github.com/dehydrated-io/dehydrated/releases/download/v${DEHYDRATED_VER}/dehydrated-${DEHYDRATED_VER}.tar.gz -O /tmp/dehydrated-${DEHYDRATED_VER}.tar.gz && \
    tar -xzf /tmp/dehydrated-${DEHYDRATED_VER}.tar.gz --directory /opt/dehydrated && \
    mkdir -p /var/www/dehydrated && \
    mkdir -p /config && \
    mkdir -p /storage

# copy ADC hooks
COPY ["citrix-adc_hooks.py", "config-adc.example", "/opt/adc-hook/"]
RUN chmod +x /opt/adc-hook/citrix-adc_hooks.py

# copy CMD script
COPY letsencrypt-start.sh /

# change execution rights
RUN chmod +x /letsencrypt-start.sh

CMD ./letsencrypt-start.sh
