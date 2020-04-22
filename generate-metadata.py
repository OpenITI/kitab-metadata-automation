"""Generate OpenITI metadata files.

The script takes as inputs:
* the uris of all text versions in the corpus
* all yml files for authors, books and versions in the corpus
* all issues in the OpenITI/Annotation GitHub repository
* a tsv file ID_TAGS.txt containing normalized tags from the source libraries
  and Brockelmann

NB: Arabic author names and book titles are taken from the yml files alone
    if the yml files contain this info; otherwise they are taken from the
    text file headers.
    => if the text file headers contain wrong metadata,
       add the correct metadata to the yml file!
    Dates are taken from the URI alone.
    

And creates the following outputs:
* OpenITI_metadata_light.csv:
    a csv file containing the metadata extracted from the URI,
    YML files and text file headers
* OpenITI_metadata_light.json:
    a json representation of the same metadata, with in addition:
    - lists of GitHub issues related to each version/book/author
    - lists of passim runs related to each version
* OpenITI_metadata_complete.yml:
    Master yml file created from all author, book and version yml files
* OpenITI_header_metadata.json:
    A json file with all the metadata from the text file headers.

"""

import csv
import json
import os
import re
import shutil
import sys
import textwrap
import time

# (in a later stage to be imported from the openiti python library):

#from utility import betaCode
from utility.betaCode import deNoise, betaCodeToArSimple
from utility import zfunc
from utility.uri import URI, check_yml_files
from utility import get_issues

#from openiti.helper.uri import check_yml_files



start = time.time()
splitter = "##RECORD"+"#"*64+"\n"
all_header_meta = dict()
VERBOSE = False

def LoadTags():
    """Load tags from the tags/genre file created by Maxim."""
    mapping_file = "./utility/ID_TAGS.txt"
    with open(mapping_file, "r", encoding="utf8") as f1:
        dic = {}
        data = f1.read().split("\n")

        for d in data:
            d = d.split("\t")
            dic[d[0]] = d[1]
    return dic

tagsDic = LoadTags()

# define a metadata category for all relevant items in the text file headers:
headings_dict = {  
     'Iso' : "Title", 
     'Lng' : "AuthorName",
     'higrid': "Date",
     'HigriD': "Date",
     'auth' : "AuthorName",
     'bk' : "Title", # 
     'cat' : "Genre", # Values: max 3-digit integer
     'name' : "Genre", 
     'البلد' : "Edition:Place", 
     'الطبعة' : "Edition:Date", # date + number (al-ula, al-thaniya, ...)
     'الكتاب' : "Title", 
     'المؤلف' : "AuthorName", 
     'المحقق' : "Edition:Editor", 
     'الناشر' : "Edition:Publisher", 
     'تأليف' : "AuthorName", 
     'تحقيق' : "Edition:Editor", 
     'تقديم وتعليق' : "Edition:Editor", 
     'حققه' : "Edition:Editor", 
     'خرج أحاديثه' : "Edition:Editor", 
     'دار النشر' : "Edition:Publisher", 
     'دراسة وتحقيق' : "Edition:Editor", 
     'سنة الطبع' : "Edition:Date", 
     'سنة النشر' : "Edition:Date", 
     'شهرته' : "AuthorName", 
     'عام النشر' : "Edition:Date", 
     'مكان النشر' : "Edition:Place", 
     'وضع حواشيه' : "Edition:Editor", 
     'أشرف عليه وراجعه وقدم له' : "Edition:Editor", # thesis supervisor
     'أصدرها':  "Edition:Editor",
     'أعتنى به' : "Edition:Editor",
     'أعد أصله' : "Edition:Editor",
     'أعده' : "Edition:Editor",
     'أعده للنشر' : "Edition:Editor",
     'أعده ونشره' : "Edition:Editor",
     'ألحقها' : "Edition:Editor",
     'تقديم وإشراف ومراجعة' : "Edition:Editor", 
     '010.AuthorAKA' : "AuthorName", 
     '010.AuthorNAME' : "AuthorName", 
     '011.AuthorDIED' : "Date", 
     '019.AuthorDIED' : "Date", 
     '020.BookTITLE' : "Title", 
     '021.BookSUBJ' : "Genre", # separated by :: 
     '029.BookTITLEalt' : "Title", 
     '040.EdEDITOR' : "Edition:Editor", 
     '043.EdPUBLISHER' : "Edition:Publisher", 
     '044.EdPLACE' : "Edition:Place", 
     '045.EdYEAR' : "Edition:Date", 
     }





def createJsonFile(csv_fp, out_fp, passim_runs, issues_uri_dict):
    """Convert the csv file into a json file,
    adding passim data and Github issues.

    Args:
        csv_fp (str): the filepath of the csv with the input data
        out_fp (str): the filepath of the output json file
        passim_runs (list): a list of 2-item lists of the
            text reuse detection algorithm passim:
            - first list member: description (date + version number)
            - second list member: run id
        issues_uri_dict (dict): a dictionary mapping containing the
            GitHub issues, sorted by URI:
                - key: uri
                - value: a list of GitHub issue objects

    Returns:
        None
    """
    json_objects = []
    webserver_url = 'http://dev.kitab-project.org'

    with open(csv_fp) as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        record = {}

        for row in reader:
            record = row
            
            # Create a URL for KITAB Web Server for SRT Files
            
            #new_id = row['url'].split('/')[-1].split('.')[-1] # may get the extension!
            uri = URI(row['url'])
            v_id = uri("version", ext="").split(".")[-1]
            record['srts'] = []
            for descr, run_id in passim_runs:
                if "2017" in descr:
                    srt_link = "/".join([webserver_url, run_id, v_id[:-5]])
                else:
                    srt_link = "/".join([webserver_url, run_id, v_id])
                record['srts'].append([descr, srt_link])

            # get issues related to the current book/version:
            
            uri = URI(row["versionUri"])
            book_issues = []
            if uri("book") in issues_uri_dict:
                book_issues = issues_uri_dict[uri("book")]
                book_issues = [[x.number, x.labels[0].name] for x in book_issues]
            author_issues = []
            if uri("author") in issues_uri_dict:
                author_issues += issues_uri_dict[uri("author")]
                author_issues = [[x.number, x.labels[0].name] for x in author_issues]
            version_issues = []
            if uri("version") in issues_uri_dict:
                version_issues = issues_uri_dict[uri("version")]
                version_issues = [[x.number, x.labels[0].name] for x in version_issues]
            record["author_issues"] = author_issues
            record["book_issues"] = book_issues
            record["version_issues"] = version_issues
            json_objects.append(record)


    # The required format for json file is data:[{jsonobjects}]
    first_json_key = {}
    first_json_key['data'] = json_objects
    with open(out_fp, 'w') as json_file:
        json.dump(first_json_key, json_file,
                  ensure_ascii=False, sort_keys=True)


def read_header(fp):
    """Read only the OpenITI header of a file without opening the entire file.

    Args:
        fp (str): path to the text file

    Returns:
        header (list): A list of all metadata lines in the header
    """
    with open(fp, mode="r", encoding="utf-8") as file:
        header = []
        line = file.readline()
        i=0
        while "#META#Header#End" not in line and i < 100:
            if "#META#" in line or "#NewRec#" in line:
                header.append(line)
            line = file.readline() # move to next line
            i += 1
    return header


def extract_metadata_from_header(fp):
    """Extract the metadata from the headers of the text files.

    Args:
        fp (str): path to the text file

    Returns:
        meta (dict): dictionary containing relevant extracted header items
    """
    header = read_header(fp)
    categories = "AuthorName Title Date Genre "
    categories += "Edition:Editor Edition:Publisher Edition:Place Edition:Date"
    meta = {x : [] for x in categories.split()}
    unreadable = []
    all_meta = dict()
    
    for line in header:
        split_line = line[7:].split("\t::")  # [7:] : start reading after #META# tag
        if len(split_line) == 1:
            split_line = line[7:].split(": ", 1)  # split after first colon
        if len(split_line) > 1:
            val = split_line[1].strip()
            if val.startswith("NO"):
                val = ""
            else:
                # remove line endings within heading categories: 
                val = re.sub(" +", "@@@", val)
                val = re.sub("\s+", "¶ ", val)
                val = re.sub("@@@", " ", val).strip()
                if val.isnumeric():
                    val = str(int(val))
            if val != "":
                key = re.sub("\# ", "", split_line[0])
                all_meta[key] = val
                # reorganize the relevant headers under overarching categories:
                if key in headings_dict:
                    cat = headings_dict[key]
                    meta[cat].append(val)
        else:
            unreadable.append(line)
    if VERBOSE:
        if unreadable:
            print(fp, "METADATA IN UNREADABLE FORMAT")
            for line in unreadable:
                print(line)
            print(meta)
            input("press enter to continue")

    
    all_header_meta[os.path.split(fp)[0]] = all_meta
    return meta

def insert_spaces(s):
    """Split the camel-case string s and insert a space before each capital."""
    return re.sub("([a-z])([A-Z])", r"\1 \2", s)

def collectMetadata(start_folder, exclude, csv_outpth, yml_outpth, incl_char_length=False):
    """Collect the metadata from URIs, YML files and text file headers
    and save the metadata in csv and yml files.

    Args:
        start_folder (str): path to the parent folder of all folders
            from which metadata should be collected
        exclude (list): list of directory names that should be excluded
            from the metadata collections
        csv_outpth (str): path to the output csv file
        yml_outpth (str): path to the output yml file
    """

    print("collecting metadata from OpenITI...")

    dataYML = []
    dataCSV = {}  # vers-uri, date, author, book, id, status, length, fullTextURLURL, instantiationURL, tags, localPath
    statusDic = {}
    split_files = dict()

    for root, dirs, files in os.walk(start_folder):
        dirs = [d for d in sorted(dirs) if d not in exclude]
        
        for file in files:
            # select only the version yml files:
            if re.search("^\d{4}[A-Za-z]+\.[A-Za-z\d]+\.\w+-(ara|per)\d\.yml$",
                         file):
                uri = URI(os.path.join(root, file))

                # build the filepaths to all yml files related
                # to the current version yml file: 
                versF = uri.build_pth(uri_type="version_yml")
                bookF = uri.build_pth(uri_type="book_yml")
                authF = uri.build_pth(uri_type="author_yml")

                # bring together all yml data related to the current version
                # and store in the master dataYML variable:
                versD = zfunc.dicToYML(zfunc.readYML(versF)) + "\n"
                bookD = zfunc.dicToYML(zfunc.readYML(bookF)) + "\n"
                authD = zfunc.dicToYML(zfunc.readYML(authF)) + "\n"
                record = splitter + versD + bookD + authD
                dataYML.append(record)

                # collect the metadata related to the current version:


                # 1) from the YML files:

                # - length in number of characters:
                versD = zfunc.readYML(versF)
                length = versD["00#VERS#LENGTH###:"].strip()
                if incl_char_length:
                    char_length = versD["00#VERS#CLENGTH##:"].strip()

                # - edition information:
                ed_info = []
                if not versD["80#VERS#BASED####:"].strip().startswith("perma")\
                   and not versD["80#VERS#BASED####:"].strip().startswith("NO"):
                    ed_info = [versD["80#VERS#BASED####:"].strip(), ]                    

                # - title:
                bookD = zfunc.readYML(bookF)
                title = []
                for c in ["10#BOOK#TITLEA#AR:", "10#BOOK#TITLEB#AR:"]:
                    if not "al-Muʾallif" in bookD[c]:
                        title.append(bookD[c].strip())
                        title.append(betaCodeToArSimple(title[-1]))
                        
                # - author:
                authD = zfunc.readYML(authF)
                shuhra = ""
                if not "Fulān" in authD["10#AUTH#SHUHRA#AR:"]:
                    shuhra = authD["10#AUTH#SHUHRA#AR:"].strip()
                name_comps = ["10#AUTH#LAQAB##AR:",
                              "10#AUTH#KUNYA##AR:",
                              "10#AUTH#ISM####AR:",
                              "10#AUTH#NASAB##AR:",
                              "10#AUTH#NISBA##AR:"]
                full_name = [authD[x] for x in name_comps \
                             if "Fulān" not in authD[x]]
                full_name = " ".join(full_name)


                # 2) from the URI: 

                # - date:
                date = uri.date

                # - author:
                author = insert_spaces(uri.author)

                # - book title:
                if not title:
                    title.append(insert_spaces(uri.title))

                # - book URI
                bookURI = uri.build_uri("book")

                # - version URI:
                versURI = uri.build_uri("version")

                # - make a provisional (i.e., without extension)
                #   local filepath  to the current version:
                uri.extension = ""
                local_pth = uri.build_pth("version_file")
                #print(local_pth)

                # - set temporary secondary status for every book.
                #   the primary version of a book is the one that
                #   has the most developed annotation
                #   (signalled by the extension: mARkdown>completed>inProgress)
                #   If no version has an extension,
                #   the longest version will provisorally be considered primary.
                #   The length comparison can take place only after all versions
                #   have been documented.
                #   For this reason, versions with an extension
                #   are provisionally given a very high number
                #   in the statusDic instead of their real length,
                #   so that they will be chosen as primary version
                #   once the lengths are compared:
                status = "sec"
                if os.path.isfile(local_pth+".inProgress"):
                    lenTemp = 100000000
                    uri.extension = "inProgress"
                elif os.path.isfile(local_pth+".completed"):
                    lenTemp = 1000000000
                    uri.extension = "completed"
                elif os.path.isfile(local_pth+".mARkdown"):
                    lenTemp = 10000000000
                    uri.extension = "mARkdown"
                elif "Sham30K" in local_pth: # give Sham30K files lowest priority
                    lenTemp = 0
                    uri.extension = ""
                else:
                    uri.extension = ""
                    if length:
                        lenTemp = length
                    else:
                        lenTemp = 0

                # - rebuild the local_path, with the extension:
                local_pth = uri.build_pth("version_file")

                # - add the uri to the statusDic if the file is not missing:
                if os.path.exists(local_pth):
                    
                    if bookURI in statusDic:
                        statusDic[bookURI].append("%012d##" % int(lenTemp) + versURI)
                    else:
                        statusDic[bookURI] = []
                        statusDic[bookURI].append("%012d##" % int(lenTemp) + versURI)


                # - build the path to the full text file on Github:
                if URI.data_in_25_year_repos:
                    uri.base_pth = "https://raw.githubusercontent.com/OpenITI"
                    fullTextURL = re.sub("data/", "master/data/", uri.build_pth("version_file"))
                else:
                    uri.base_pth = "data"
                    fullTextURL = uri.build_pth("version_file")

                # - tags (for extension + "genres")
                tags = ""
                if uri.extension:
                    tags += uri.extension.upper()+","
                if uri.version in tagsDic:
                    tags += tagsDic[uri.version]
                    #print(uri.version, tagsDic[uri.version])


                # 3) collect additional metadata (mostly in Arabic!)
                #    from the text file headers:
                
                
                if not os.path.exists(local_pth):
                    print("MISSING FILE? {} does not exist".format(local_pth))
                else:
                    header_meta = extract_metadata_from_header(local_pth)
                    #print(local_pth, header_meta)

                    # - author name (combine with the uri's author component)
                    add_arabic_name = True
                    if shuhra:
                        author.append(shuhra)
                        author.append(betaCodeToArSimple(shuhra))
                        print(betaCodeToArSimple(shuhra))
                        add_arabic_name = False
                    if full_name:
                        author.append(full_name)
                        author.append(betaCodeToArSimple(full_name))
                        add_arabic_name = False
                    if add_arabic_name:
                        author = [author,] + list(set(header_meta["AuthorName"]))

                    # - book title (combine with the uri's title component)
                    if len(title) < 2: # if no title was taken from the YML file
                        title += list(set(header_meta["Title"]))

                    # - information about the current version's edition: 
                    ed_info = header_meta["Edition:Editor"] +\
                              header_meta["Edition:Place"] +\
                              header_meta["Edition:Date"] +\
                              header_meta["Edition:Publisher"] +\
                              ed_info

                    # - additional genre tags: 
                    tags = tags.split(",") + list(set(header_meta["Genre"]))

                    # if there are multiple values: separate with " :: ":
                    cats = [author, title, ed_info, tags]
                    author, title, ed_info, tags = [" :: ".join(x) for x in cats]
                    
                    # compile the data in a tsv line and store in dataCSV dict:
                    v = [versURI, date, author, bookURI, title, ed_info,
                         uri.version, status, length, fullTextURL, tags,]
                    if incl_char_length:
                        v.append(char_length)
                    value = "\t".join(v)
                    dataCSV[versURI] = value

                # Deal with files split into multiple parts because
                # they were too big: 
                if re.search("Vols[A-Z]-", versURI):
                    print(versURI)
                    m = re.sub("Vols[A-Z]", "", versURI)
                    if m not in split_files:
                        split_files[m] = []
                    split_files[m].append(versURI)


    # Give primary status to "longest" version:
    for k, v in statusDic.items():
        v = sorted(v, reverse=True)
        key = v[0].split("##")[1]
        dataCSV[key] = dataCSV[key].replace("\tsec\t", "\tpri\t")


    # Write a json file containing all texts that have been split
    # into parts because they were too big (URIs with VolsA, VolsB, ...):
    split_files_fp = re.sub("metadata_light.csv", "split_files.json", csv_outpth)
    with open(split_files_fp, mode='w', encoding='utf-8') as outfile:
        json.dump(split_files, outfile, indent=4)  

    # add data for files split into multiple parts:
    for file in split_files:
##        print(file, "consists of mutltiple files:")
##        print(split_files[file])
        first_part = split_files[file][0]
        file_length = 0
        file_clength = 0
        for part in split_files[file]:
            # make each part a primary version: 
            dataCSV[part] = dataCSV[part].replace("\tsec\t", "\tpri\t")
            # collect the token and character length from each part
            file_length += int(dataCSV[part].split("\t")[8])
            if incl_char_length:
                file_clength += int(dataCSV[part].split("\t")[-1])
        # add an extra line to the csv data with metadata of the compound file: 
        file_csv_line = dataCSV[first_part].split("\t")
        file_csv_line[0] = file
        file_csv_line[6] = re.sub("Vols[A-Z]", "", file_csv_line[6])
        file_csv_line[7] = "sec"
        file_csv_line[8] = str(file_length)
        file_csv_line[9] = re.sub("Vols[A-Z]", "", file_csv_line[9]) # fullTextURL
        if incl_char_length:
            file_csv_line[-1] = str(file_clength)
        file_csv_line = "\t".join(file_csv_line)
        dataCSV[file] = file_csv_line      

    # Sort the tsv data and save it to file: 
    dataCSV_New = []
    for k, v in dataCSV.items():
        #print("\t"+k)
        dataCSV_New.append(v)
    dataCSV = sorted(dataCSV_New)

    print("="*80)
    print("COLLECTING INTO A CSV FILE ({} LINES)...".format(len(dataCSV)))
    print("="*80)

    h = ["versionUri", "date", "author", "book",
                        "title", "ed_info", "id", "status",
                        "tok_length", "url",
                        #"instantiation", "localPath",
                        "tags", ]
    if incl_char_length:
        h.append("char_length")
    header = "\t".join(h)
    
    with open(csv_outpth, "w", encoding="utf8") as outfile:
        outfile.write(header+"\n"+"\n".join(dataCSV))#.replace(" ", ""))

    # Finally, also save the combined yml data in a master yml file: 
    with open(yml_outpth, "w", encoding="utf8") as outfile:
        outfile.write("\n".join(dataYML))




        
        



#URI.data_in_25_year_repos = False

corpus_path = "../OpenITI"
corpus_path = r"D:\London\OpenITI\25Y_repos"
msg = "Insert the path to the parent folder of the repos: "
corpus_path = input(msg)
print("Metadata will be collected in", corpus_path)

print("Is the data in 25-years folders? (press 'N' for RELEASE data)")
resp = input("Y/N: ")
if resp.upper() == "N":
    URI.data_in_25_year_repos = False
else:
    URI.data_in_25_year_repos = True

exclude = (["OpenITI.github.io", "Annotation", "maintenance", "i.mech00",
            "i.mech01", "i.mech02", "i.mech03", "i.mech04", "i.mech05",
            "i.mech06", "i.mech07", "i.mech08", "i.mech09", "i.logic",
            "i.cex", "i.cex_Temp", "i.mech", "i.mech_Temp", ".git"])


# 0- first, check and update yml files:

print("Do you want to check completeness of the yml files?")
resp = input("Y/N: ")
if resp == "Y":
    print("Do you want to re-calculate the Arabic token length of every text?")
    print("This may take up to an hour on a slow machine.")
    resp = input("Y/N: ")
    if resp == "Y":
        check_token_counts = True
    else:
        check_token_counts = False

    print("Checking yml files before collecting metadata...")
    # execute=False forces the script to show you all changes it wants to make
    # before prompting you whether to execute the proposed changes:
    check_yml_files(corpus_path, exclude=exclude,
                    execute=False, check_token_counts=check_token_counts)
    print()


# 1- collect metadata and save to csv:

print("Do you want to include character count in addition to token count?")
resp = input("Y/N: ")
if resp.upper() == "Y":
    incl_char_length = True
else:
    incl_char_length = False

output_path = "./output/"
##parent_folder = os.path.split(corpus_path)[-1]
##if not parent_folder:
##    parent_folder = os.path.split(os.path.split(corpus_path)[0])[-1]
pth_string = re.sub("\.+[\\/]", "", corpus_path)
pth_string = re.sub(r"[\\/]", "_", pth_string)
meta_csv_fp = output_path + pth_string + "_metadata_light.csv"
meta_yml_fp = output_path + pth_string + "_metadata_complete.yml"
print(meta_csv_fp)
collectMetadata(corpus_path, exclude, meta_csv_fp, meta_yml_fp,
                incl_char_length=incl_char_length)
end = time.time()
print("Processing time: {0:.2f} sec".format(end - start))

print("="*80)
print("CREATING JSON FILE...")
print("="*80)

# 2a - collect issues from GitHub:

# try reading the github access token from file:
# NB: if you put the access token in a file, make sure
#     to put the filename into the .gitignore file,
#     in order not to expose it: 
try:
    with open("GitHub personalAccessTokenReadOnly.txt",
              mode="r", encoding="utf-8") as file:
        github_token = file.read().strip()
except:
    github_token = None # you will be prompted to insert the token manually

issues = get_issues.get_issues("OpenITI/Annotation",
                               access_token=github_token,
                               issue_labels=["URI change suggestion",
                                             "text quality",
                                             "PRI & SEC Versions"])
issues = get_issues.define_text_uris(issues)
issues_uri_dict = get_issues.sort_issues_by_uri(issues)


# 2b - create a json file from the csv data:

out_fp = output_path + pth_string + '_metadata_light.json'
passim_runs = [['October 2017 (V1)', 'passim1017'],
               ['February 2019 (V2)', 'passim01022019'],
               ['May 2019 (Aggregated)', 'aggregated01052019']]
createJsonFile(meta_csv_fp, out_fp, passim_runs, issues_uri_dict)

# 3 - Save all metadata in the text file headers to a separate json file:

outfp = output_path + pth_string + "_header_metadata.json"
with open(outfp, mode="w", encoding="utf-8") as file:
    json.dump(all_header_meta, file, ensure_ascii=False)

print("Tada!")

# commit changes in repos
resp = input("Commit changes in repos and push to GitHub? Y/N: ")

if resp.upper() == "Y":
    print("Use default commit message?")
    msg = "Updated yml files during automatic metadata creation."
    print("    '{}'".format(msg))
    resp = input("Y/N: ")
    if resp.upper() == "N":
        msg = input("Write commit message: ")
        

    import subprocess
    for repo in os.listdir(corpus_path):
        repo_pth = os.path.join(corpus_path, repo)
        p = subprocess.Popen(["git", "add", "."], cwd=repo_pth)
        p.wait()
        p = subprocess.Popen(["git", "commit", "-m", msg], cwd=repo_pth)
        p.wait()
        p = subprocess.Popen(["git", "push", "origin", "master"], cwd=repo_pth)
        p.wait()
        print()

