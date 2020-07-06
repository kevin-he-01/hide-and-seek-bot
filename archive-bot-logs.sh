#! /usr/bin/env bash

if (( $# < 1 )); then
    echo Insufficient arguments >&2
    exit 1
fi

logs="$(echo bot/{common,hider,seeker}.log)"

# for log in $logs; do
#     echo -n > $log
# done
# echo $logs

# Note: also removes prevous notes, like clear-log and a save
name="saved-bot-logs/$1/"
mkdir "$name"
mv $logs "$name"

# Recreate empty log files
touch $logs