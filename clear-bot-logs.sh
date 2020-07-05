#! /usr/bin/env bash

logs="$(echo bot/{common,hider,seeker}.log)"

for log in $logs; do
    echo -n > $log
done
