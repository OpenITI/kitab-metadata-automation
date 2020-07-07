#!/bin/bash
clear

#Path of the folder where corpus files are stored
#echo "Enter the path to the corpus "
CORPUSPATH="/home/admin-kitab/Documents/OpenITI/GitHub_clone"
#echo $CORPUSPATH

cd $CORPUSPATH
pwd

echo "Resetting local changes ..."
ls | xargs -P10 -I{} git -C {} reset --hard

echo "Fetching changes from corpus ..."
ls | xargs -P10 -I{} git -C {} pull origin 

#Path of the folder where python script is located
#echo "Enter the path to the script "
ROOTPATH="/home/admin-kitab/Documents/Projects/kitab-metadata-automation"
#echo $ROOTPATH

cd $ROOTPATH
pwd

echo "Generating corpus metadata  ..."
python3 generate-metadata.py -c ./utility/config-automated-do-not-remove-or-change.py

# echo "Committing changes to repo ..."
git config user.email kitab-project@outlook.com
git config user.name 'KITAB Project'
git add .
git commit -m 'output generated' 
git push


