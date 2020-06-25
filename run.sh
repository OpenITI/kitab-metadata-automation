#!/bin/bash
clear

# Path of the folder where corpus files are stored
echo "Enter the path to the corpus "
# CORPUSPATH="/home/admin-kitab/Documents/OpenITI/GitHub_clone"
read CORPUSPATH
echo "Resetting local changes ..."
# echo $CORPUSPATH
cd "$CORPUSPATH"
#exec /bin/bash

ls | xargs -P10 -I{} git -C {} reset --hard

echo "Fetching changes from corpus ..."
ls | xargs -P10 -I{} git -C {} fetch origin 

# Path of the folder where python script is located
echo "Enter the path to the script "
# ROOTPATH="/home/admin-kitab/Documents/Codes/kitab-metadata-automation"
read ROOTPATH
cd "$ROOTPATH"

# exec /bin/bash

echo "Generating corpus metadata  ..."
python3 generate-OpenITI-metadata.py

echo "Committing changes to repo ..."
git commit -a -m 'output generated'
git push 

