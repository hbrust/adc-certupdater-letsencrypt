#!/bin/bash
# copy example config if config dir empty (= first run)
if  [ -z "$(ls -A -- /config)" ]; then
  cp /opt/adc-hook/config-adc.example /config/
  cp /opt/dehydrated/docs/examples/domains.txt /config/
fi

# main loop every 5 minutes
while [ 1 ]; do 
   for cfg in /config/*.cfg; do
       # break out if no config file available
       if [ ! -f "$cfg" ]; then
          echo "INFO ($(date)): NO CONFIG FILE IN CONFIG DIRECTORY! CONFIG FILE NEEDS '.cfg' EXTENSION."
          continue
       fi
       export CONFIG="$cfg"
       registertxt="To use dehydrated with this certificate authority you have to agree to their terms of service which you can find here" 
       /opt/dehydrated/dehydrated -c -f $cfg 2>&1 | tee /tmp/lastrun
       # check for need of registering
       grep -q "$registertxt" /tmp/lastrun
       if [ $? == 0 ]; then
          echo "INFO: register account"
          /opt/dehydrated/dehydrated --register --accept-terms
          /opt/dehydrated/dehydrated -c -f $cfg
       fi
       unset CONFIG
   done
   # wait 5min
   sleep 300
done


