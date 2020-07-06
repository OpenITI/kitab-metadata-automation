#!/bin/bash
clear

# Path of the folder where corpus files are stored
#echo "Enter the path to the corpus "
#CORPUSPATH="/home/admin-kitab/Documents/OpenITI/GitHub_clone"
#read CORPUSPATH
#echo $CORPUSPATH
#exec /bin/bash
cd /home/admin-kitab/Documents/OpenITI/Github_clone
pwd
ROOTPATH="//home/admin-kitab/Documents/Projects/kitab-metadata-automation"
cd $ROOTPATH
pwd

echo "Generating corpus metadata  ..."
python3 generate-metadata.py -c ./utility/config_corpus.py

# #cd "$CORPUSPATH"
# ls

# echo "Resetting local changes ..."




# #ls | xargs -P10 -I{} git -C {} reset --hard

# #echo "Fetching changes from corpus ..."
# #ls | xargs -P10 -I{} git -C {} fetch origin 

# # Path of the folder where python script is located
# #echo "Enter the path to the script "
# ROOTPATH="//home/admin-kitab/Documents/Projects/kitab-metadata-automation"
# read ROOTPATH
# cd "$ROOTPATH"
# exec /bin/bash

# echo "Generating corpus metadata  ..."
# python3 generate-metadata.py -c ./utility/config_corpus.py

# echo "Committing changes to repo ..."
# #git commit -a -m 'output generated'
# #git push 

