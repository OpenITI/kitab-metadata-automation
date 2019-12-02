#!/bin/bash
clear

CORPUSPATH="/mnt/c/Development Work/KITAB/OpenITI"
echo "Resetting local changes ..."
echo $CORPUSPATH
cd "$CORPUSPATH"
#exec /bin/bash

ls | xargs -P10 -I{} git -C {} reset --hard

echo "Fetching changes from corpus ..."
ls | xargs -P10 -I{} git -C {} fetch origin 

ROOTPATH="/mnt/c/Development Work/KITAB/kitab-metadata-automation"
cd "$ROOTPATH"
# exec /bin/bash

echo "Generating corpus metadata  ..."
#python3 generate-OpenITI-metadata.py

echo "Committing changes to repo ..."
git commit -a -m 'output generated'
git push 

