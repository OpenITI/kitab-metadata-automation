from openiti.helper.ara import ar_tok, ar_char
from openiti.helper.funcs import get_all_text_files_in_folder
from openiti.helper.uri import URI
from openiti.helper.yml import readYML, dicToYML

import re
from urllib.parse import unquote
import os

def check_yml_validity(folder,
                       yml_types=["version_yml", "book_yml", "author_yml"]):
    for v_fp in get_all_text_files_in_folder(folder):
        for t in yml_types:
            yml_fp = URI(v_fp).build_pth(t)
            try:
                if os.path.exists(yml_fp):
                    readYML(yml_fp)
            except:
                print(yml_fp)
    print("yml check finished")

check_yml_validity("/home/admin-kitab/Documents/OpenITI/RELEASE_git/working_dir/AH_repos",yml_types=["version_yml", "book_yml", "author_yml"])
