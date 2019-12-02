# kitab-metadata-automation
KITAB metadata automation

## Shell Script
1) Delete any local changes made to the corpus (just in case) 
``ls | xargs -P10 -I{} git -C {} reset --hard ``

2) Fetch all the repos to make sure that metadata is generated based on the lastest version of the corpus
``ls | xargs -P10 -I{} git -C {} fetch origin ``

3) Generate metadata python script
``python3 generate-OpenITI-metadata.py``

4) Push the file generated (output) to repo (e.g. maintenance)

``git commit -a -m 'output generated' ``
``git push ``

## Cron Job
- Run the Shell Sript on every Sunday at 4:00am
- Log the the process


``* 4 * * 0 ./run.sh >> output.log``
