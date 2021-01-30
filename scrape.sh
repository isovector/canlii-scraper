#!/bin/bash

while :; do
  rm -rf /tmp/*
  wmctrl -c "Firefox"
  pkill canlii
  pkill java
  pkill gecko
  java -jar selenium.jar &
  mullvad relay set relay `cat relays| shuf | head -n1`
  sleep 20s
  stack run &
  sleep 2s
  python2 canlii.py
done


