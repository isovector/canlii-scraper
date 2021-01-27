#!/bin/bash

java -jar selenium.jar &

while :; do
  mullvad relay set relay `cat relays| shuf | head -n1`
  sleep 5s
  stack run &
  sleep 2s
  python2 canlii.py
  pkill canlii
done


