import os
import re

from openiti.helper.uri import URI
from openiti.helper.ara import ar_cnt_file

def collect_char_len(start_folder, exclude, csv_outpth):
    """Collect the character length of all texts in the corpus into a csv."""
    print("Collecting character lengths...")
    print("This will take a while!")
    cnt = []
    for root, dirs, files in os.walk(start_folder):
        dirs[:] = [d for d in sorted(dirs) if d not in exclude]
        for file in files:
            if re.search("^\d{4}[A-Za-z]+\.[A-Za-z\d]+\.\w+-(ara|per)\d\.yml$",
                         file):
                print(file)
                version_uri = URI(os.path.join(root, file))
                for ext in ["mARkdown", "completed", "inProgress", ""]:
                    version_uri.extension = ext
                    fp = version_uri.build_pth(uri_type="version_file")
                    if os.path.exists(fp):
                        break
                char_count = ar_cnt_file(fp, mode="char")
                uri = version_uri.build_uri(ext="")
                cnt.append("\t".join([uri, fp, str(char_count)]))
    with open(csv_outpth, mode="w", encoding="utf-8") as file:
        file.write("\n".join(cnt))
    print("csv written to", csv_outpth)


msg = "Insert the path to the parent folder of the 25-years repos: "
corpus_path = input(msg)

exclude = (["OpenITI.github.io", "Annotation", "maintenance", "i.mech00",
            "i.mech01", "i.mech02", "i.mech03", "i.mech04", "i.mech05",
            "i.mech06", "i.mech07", "i.mech08", "i.mech09", "i.logic",
            "i.cex", "i.cex_Temp", "i.mech", "i.mech_Temp", ".git"])

output_path = "./output/"
output_path = "./output/test/"

csv_outpth = output_path+"character_count.csv"

collect_char_len(corpus_path, exclude, csv_outpth)
                
        
