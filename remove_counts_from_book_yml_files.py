#from openiti.helper.funcs import get_all_text_files_in_folder
from openiti.helper.yml import readYML, dicToYML
import os
import re

def get_all_text_files_in_folder(start_folder):
    for root, dirs, files in os.walk(start_folder):
        for fn in files:
            if re.findall(r"-\w\w\w\d(?:.inProgress|.completed|.mARkdown)?\Z", fn):
                fp = os.path.join(root, fn)
                yield(fp) 




folder = "~/Documents/OpenITI/RELEASE_git/working_dir/AH_repos"
folder = "/home/admin-kitab/Documents/OpenITI/RELEASE_git/working_dir/AH_repos"

print(folder)
print(len([x for x in get_all_text_files_in_folder(folder)]))
for fp in get_all_text_files_in_folder(folder):
#    print("fp:", fp)
    if fp.endswith(("mARkdown", "inProgress", "completed")):
        book_yml = ".".join(fp.split(".")[:-2])+".yml"
    else:
        book_yml = ".".join(fp.split(".")[:-1])+".yml"
#    print(">", book_yml)
    try:
        d = readYML(book_yml)
        #print(dicToYML(d))
        if "00#VERS#CLENGTH##:" in d: 
            #print("*"*30)
            print(book_yml) 
            #print(dicToYML(d)) 
            #print(">"*10) 
            del d["00#VERS#CLENGTH##:"] 
            del d["00#VERS#LENGTH###:"] 
            #print(dicToYML(d)) 
            with open(book_yml, mode="w", encoding="utf-8") as file:
                file.write(dicToYML(d))
#            input("CONTINUE?")

    except Exception as e:
        print("-"*30)
        print(fp)
        print(book_yml)
#    input("CONTINUE?")
