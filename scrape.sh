#!/bin/bash


while :; do
  java -jar selenium.jar &
  mullvad relay set relay `cat relays| shuf | head -n1`
  sleep 20s
  stack run &
  sleep 2s
  python2 canlii.py
  wmctrl -c "| CanLII"
  pkill canlii
  pkill java
done


