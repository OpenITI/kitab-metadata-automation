"""Generate OpenITI metadata files.

The script is best run from the command line.

You can adapt the parameters in a number of ways:

* by adapting the default config file (utility/config.py)
  (restore default by running `python generate-metadata.py -d`)
* by providing a custom config file:
  `python generate-metadata.py -c D:/OpenITI/RELEASE_config.py`
* by specifying command-line arguments (see example below)
* by running the script with default configurations
  (`python generate-metadata.py`)
  and replying to the questions when prompted (see example below)

NB: the script now works with the traditional OpenITI repos
    as well as manuscript/document repo(s)

Examples:
    $ python3 generate-metadata.py --help
    Command line arguments for generate-metadata.py:

    -h, --help : print help info
    -t, --token_counts : update token counts
                         => sets check_token_counts variable to True
    -l, --char_length : update character counts
                        => sets incl_char_length to True
    -f, --flat_data : data not in 25 year repos
                      => sets data_in_25_year_repos to False
    -d, --restore_default : restore values in config.py to default
    -r, --recheck_yml : include a check of whether all yml files are complete

    -i, --input_folder : (str) path to the input folder
                               => sets corpus_path variable
    -o, --output_folder : (str) path to the output folder for metadata files
                                => sets output_path variable
                                (default = "./output/")
    -t, --tsv_fp : (str) file path to the tsv output file
                         (only if you do not want it in the defined output folder)
                         => sets meta_tsv_fp variable
    -y, --yml_fp : (str) file path to the yml output file
                         (only if you do not want it in the defined output folder)
                         => sets meta_yml_fp variable
    -j, --json_fp : (str) file path to the json output file
                          (only if you do not want it in the defined output folder)
                          => sets out_fp variable
    -a, --arab_header_fp: (str) file path to the json file 
                                that will contain all Arabic metadata 
                                extracted from text file headers.
                                (only if you do not want it in the defined output folder)
                                => sets meta_header_fp variable
    -x, --exclude : (list) list of folder names to exclude from metadata
    -c, --config : (str) name of a python file with custom configuration variables
                         (default: ./utility/config.py)

    # run the script with custom config file (model: utility/config.py):
    
    $ python3 generate-metadata.py -c utility/config_RELEASE.py

    # run the script with default configuration and add variables:
    
    $ python3 generate-metadata.py -i ../RELEASE/data_temp -f -r -t -l

    # run the script with default configuration; you will be prompted
    # to provide answers to configure the metadata generation:
    
    $ python3 generate-metadata.py
    Insert the path to the parent folder of the repos: ../RELEASE/data_temp
    Metadata will be collected in ../RELEASE/data_temp
    Is the data in 25-years folders? (press 'N' for RELEASE data)
    N/Y? N
    Do you want to check completeness of the yml files?
    N/Y? Y
    Do you want to re-calculate the Arabic token length of every text?
    This may take up to an hour on a slow machine.
    Y/N: Y
    Do you want to include character count in addition to token count?
    N/Y? Y

The script takes as inputs:
* the uris of all text versions / transcriptions in the corpus
* all yml files for authors, books and versions
  (and locations, manuscripts and transcriptions) in the corpus
* all issues in the OpenITI/Annotation GitHub repository
* a tsv file ID_TAGS.txt containing normalized tags from the source libraries
  and Brockelmann

NB:
  - Arabic author names and book titles are taken from the yml files alone
    if the yml files contain this info; otherwise they are taken from the
    text file headers.
    => if the text file headers contain wrong metadata,
       add the correct metadata to the yml file!
  - Dates are taken from the URI alone.
    

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
import configparser
import json
import os
import re
import shutil
import sys
import textwrap
import time
import getopt
from datetime import datetime
import copy


# (in a later stage to be imported from the openiti python library):

#from utility import betaCode
#from utility.betaCode import deNoise, betaCodeToArSimple
#from utility import zfunc  # functions used: zfunc.readYML, zfunc.dicToYML
#from utility.uri import URI, check_yml_files
#from utility import get_issues

from openiti.helper.uri import URI, check_yml_files
from openiti.git import get_issues
from openiti.helper.yml import readYML, dicToYML, fix_broken_yml
from openiti.helper.ara import deNoise, ar_cnt_file
from openiti.helper.funcs import read_text
from utility.betaCode import betaCodeToArSimple


splitter = "##RECORD"+"#"*64+"\n"
all_header_meta = dict()
version_ids = dict()
geo_URIs = dict()
VERBOSE = False

# regex patterns to ignore tokens that contain letters and numbers
# but should not be counted as tokens:
not_tok_regexes = [
    # structural tags like ### |EDITOR|, ### |PARATEXT|:
    r"[|$][A-Z]+[|$]",
    # semantic tags:
    r"@",
    r"\bY[A-Z]?\d+\b",
    # page number tags: 
    r"(?:Folio|Page)(?:Beg|Beginning|End)?V",
    # milestone tags:
    r"\bms[A-Z]?\d+",
    # markdown image links and urls:
    r"!?\[[^\]]*\]\([^)]*\)",
    # numbers only should be counted as token,
    # but not number+non-letter character (e.g., 1., (1), ...):
    r"^\W*\d+\W+$"
    ]
do_not_count = "|".join(not_tok_regexes)

# regular expression to split the text into tokens:
# NB: "|" is used for "### |PARATEXT|"-style tags and for markdown tables
tok_splitter = r"((?:\|[A-Z]+\|)|[\s~#|]+)"

filename_splitter = r"-(?:[a-z]{3}\d)+(\.(mARkdown|inProgress|completed))?$"

def count_toks(text, incl_chars=False, return_tok_set=False,
               tok_splitter=tok_splitter, do_not_count=do_not_count):
    """Count non-tag tokens in text.
    If `incl_chars`, the function will return both token and character counts.

    Args:
        text (str): text or path to text
        incl_chars (bool): if True, both tokens and characters will be counted.
           Defaults to False (count only tokens).
        tok_splitter (str): regex pattern on which the text should be split
           into tokens and non-tokens
        do_not_count (str): regex pattern to ignore tokens that contain
           letters and numbers but should not be counted as tokens

    Returns: int or (int, int)

    Examples:
        >>> text = 'This contains 4 tokens'
        >>> count_toks(text)
        4
        >>> count_toks(text, incl_chars=True)
        (4, 19)
        >>> text = 'Tags are not counted: PageV01P234 @P02 @TOP2 YB1234'
        >>> count_toks(text)
        4
        >>> text = '''Neither are markdown links: ![caption](path/to/image.png) [link](https://url.com)'''
        >>> count_toks(text)
        4
        >>> text = '''words split with hy-
phen are counted as a single token'''
        >>> count_toks(text)
        10
        >>> text = '''1. list numbers and footnote references (2) are not counted [3].'''
        >>> count_toks(text)
        8
        >>> text = '''
        |Tables|should not|
        |be a | problem|
        '''
        >>> count_toks(text)
        6
    """
    if os.path.isfile(text):
        text = read_text(text, remove_header=True)

    all_toks = re.split(tok_splitter, text)

    n_toks = 0
    n_chars = 0
    tok_set = set()
    for tok in all_toks:
        if re.findall(r"\w", tok) and not re.findall(do_not_count, tok):
            # do not count first half of hyphenated token at end of line:
            if not tok.endswith("-"):
                n_toks += 1
            if incl_chars:
                n_chars += len(re.findall(r"\w", tok))
            if return_tok_set:
                tok_set.add(tok)

    if incl_chars:
        if return_tok_set:
            return n_toks, n_chars, tok_set
        else:
            return n_toks, n_chars
    else:
        if return_tok_set:
            return n_toks, tok_set
        else:
            return n_toks

def LoadTags():
    """Load tags from the tags/genre file created by Maxim."""
    mapping_file = "./utility/ID_TAGS.txt"
    with open(mapping_file, "r", encoding="utf8") as f1:
        dic = {}
        data = f1.read().split("\n")

        for row in data:
            id_, tags = row.split("\t")
            #dic[d[0]] = re.sub(r";", " :: ", d[1])
            dic[id_] = tags.split(";")
    return dic

tags_dic = LoadTags()

# define a metadata category for all relevant items in the text file headers:
headings_dict = {  
     'Iso' : "Title", 
     'Lng' : "AuthorName",
     'higrid': "Date",
     'HigriD': "Date",
     'auth' : "AuthorName",
     'auth.x' : "AuthorName",
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
     '001.AuthorNAME' : "AuthorName",
     '011.AuthorDIED' : "Date", 
     '019.AuthorDIED' : "Date",
     '006.AuthorDIED' : "Date", 
     '020.BookTITLE' : "Title",
     '010.BookTITLE' : "Title",
     '021.BookSUBJ' : "Genre", # separated by :: 
     '029.BookTITLEalt' : "Title", 
     '040.EdEDITOR' : "Edition:Editor", 
     '043.EdPUBLISHER' : "Edition:Publisher",
     '013.EdPUBLISHER' : "Edition:Publisher",
     '044.EdPLACE' : "Edition:Place", 
     '045.EdYEAR' : "Edition:Date",
     '015.BookGENRE' : "Genre",
     'title' : "Title",
     'title_ar': "Title",
     'نام كتاب': "Title",
     'نويسنده': "AuthorName",
     'ناشر' : "Edition:Publisher",
     'تاريخ نشر' : "Edition:Date",
     'مكان چاپ' : "Edition:Place",
     'محقق/ مصحح' : "Edition:Editor",
     'مصحح' : "Edition:Editor",
     'محقق' : "Edition:Editor",
     'تاريخ نشر' : "Edition:Date",
     'تاريخ وفات مؤلف' : "Date",
     'موضوع' : "Genre",
     'Title' : "Title",
     'title' : "Title",
     'Editor': "Edition:Editor",
     'Publisher': "Edition:Publisher",
     'Place of Publication': "Edition:Place",
     'Date of Publication': "Edition:Date",
     'Author': "AuthorName",
     'author': "AuthorName",
     'source': "Edition:Place",  # in PAL texts: manuscript data
     'Date': "Date",
     }


def load_srt_meta(srt_folder, passim_runs):
    """Create a dictionary for all existing srt files for every OpenITI text.

    Args:
       srt_folder (str): path to the folder in which the html files
          for each passim run containing links to all srt file folders are saved
        passim_runs (list): a list of 2-item lists of the
            text reuse detection algorithm passim:
            - first list member: description (date + version number)
            - second list member: run id

    Returns:
        dict (key: bare id of a text (without Vols, -ara/per/..., extension, ...);
              value: list (each item is a list with two items:
                           date of the passim run, link to the relevant srt folder)
    """
    srt_d = dict()
    u = "http://dev.kitab-project.org"
    runs = {item[1]: item[0] for item in passim_runs}
    for fn in os.listdir(srt_folder):
        if fn[:-5] in runs:

            # extract text ids from html file and add their links to `srt_d`
            fp = os.path.join(srt_folder, fn)
            with open(fp, mode="r", encoding="utf-8") as file:
                html = file.read()
            ids = re.findall(r'<a href="(?:http://dev.kitab-project.org/passim\d+/)?([^\-"]+-[^"]+)"', html)
            #print(len(ids))
            for id_ in ids:
                #id_ = re.sub(r"Vols[A-Z]*|BK\d+", "", id_)
                bare_id = id_.split("-")[0]
                if not bare_id in srt_d:
                    srt_d[bare_id] = []
                srt_d[bare_id].append([runs[fn[:-5]], "/".join([u, fn[:-5], id_])])

    # sort by year and month:
    year_regex = r"(?<=passim\d{4})\d{4}"
    month_regex = r"(?<=passim\d{2})\d{2}"
    srt_d = {k: sorted(v, key = lambda x: (re.findall(year_regex, x[1]), re.findall(month_regex, x[1]))) for k,v in srt_d.items()}
    return srt_d


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
##    webserver_url = 'http://dev.kitab-project.org'
    srt_d = load_srt_meta("./utility/srt/", passim_runs)

    with open(csv_fp, mode="r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        record = {}

        for row in reader:
            record = row

            # Create a URL for KITAB Web Server for SRT Files

            #new_id = row['url'].split('/')[-1].split('.')[-1] # may get the extension!
            uri = URI(row['url'])
            if "version" in uri.uri_type:
                v_id = uri("version", ext="").split(".")[-1]
            else:
                v_id = uri("transcription", ext="").split(".")[-1]
##            bare_id = re.sub(r"Vols[A-Z]*|BK\d+", "", v_id)
##            bare_id = bare_id.split("-")[0]

            srts = []

            # get all srt files connected to the current version ID:
            bare_id = v_id.split("-")[0]
            if bare_id in srt_d:
                srts += srt_d[bare_id]
            # add srt files connected to previous versions of this text,
            # before it was split into different parts or joined with other texts:
            bare_id = re.sub(r"Vols[A-Z]*|BK\d+", "", bare_id)
            if bare_id in srt_d:
                old_srts = [x for x in srt_d[bare_id] if x not in srts]
                srts = old_srts + srts
            record["srts"] = srts
##            try:
##                record["srts"] = srt_d[bare_id]
##            except:
##                print("no srt files found for", bare_id)
##                record["srts"] = []
##            record['srts'] = []
##            if passim_runs:
##                for descr, run_id in passim_runs:
##                    if "2017" in descr:
##                        srt_link = "/".join([webserver_url, run_id, v_id[:-5]])
##                    else:
##                        srt_link = "/".join([webserver_url, run_id, v_id])
##                    record['srts'].append([descr, srt_link])

            # get issues related to the current book/version:
            if "version" in uri.uri_type:
                uri = URI(row["versionUri"])
                book_issues = []
                if uri("book") in issues_uri_dict:
                    book_issues = issues_uri_dict[uri("book")]
                    book_issues = [[x.number, x.labels[0].name] for x in book_issues]
                    print(uri("book"), book_issues)
                author_issues = []
                if uri("author") in issues_uri_dict:
                    author_issues += issues_uri_dict[uri("author")]
                    author_issues = [[x.number, x.labels[0].name] for x in author_issues]
                    print(uri("author"), author_issues)
                version_issues = []
                if uri("version") in issues_uri_dict:
                    version_issues = issues_uri_dict[uri("version")]
                    version_issues = [[x.number, x.labels[0].name] for x in version_issues]
                    print(uri("version"), version_issues)
                record["author_issues"] = author_issues
                record["book_issues"] = book_issues
                record["version_issues"] = version_issues
                json_objects.append(record)
            else:
                uri = URI(row["versionUri"])
                manuscr_issues = []
                if uri("manuscript") in issues_uri_dict:
                    manuscr_issues = issues_uri_dict[uri("manuscript")]
                    manuscr_issues = [[x.number, x.labels[0].name] for x in manuscr_issues]
                    print(uri("manuscript"), manuscr_issues)
                loc_issues = []
                if uri("location") in issues_uri_dict:
                    loc_issues += issues_uri_dict[uri("location")]
                    loc_issues = [[x.number, x.labels[0].name] for x in loc_issues]
                    print(uri("location"), loc_issues)
                transcr_issues = []
                if uri("transcription") in issues_uri_dict:
                    transcr_issues = issues_uri_dict[uri("transcription")]
                    transcr_issues = [[x.number, x.labels[0].name] for x in transcr_issues]
                    print(uri("transcription"), transcr_issues)
                record["location_issues"] = loc_issues
                record["manuscript_issues"] = manuscr_issues
                record["transcription_issues"] = transcr_issues
                json_objects.append(record)



    # The required format for json file is data:[{jsonobjects}]
    first_json_key = {}
    first_json_key['data'] = json_objects
    first_json_key['date'] = datetime.now().strftime("%d %B %Y")
    first_json_key['time'] = datetime.now().strftime("%H:%M:%S")
    #print("first_json_key['date']", first_json_key['date'])
    with open(out_fp, 'w', encoding="utf-8") as json_file:
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
                val = re.sub(r" +", "@@@", val)
                val = re.sub(r"\s+", "¶ ", val)
                val = re.sub(r"@@@", " ", val).strip()
                if val.isnumeric():
                    val = str(int(val))
            if val != "":
                key = re.sub(r"\# ", "", split_line[0])
                all_meta[key] = val
                # reorganize the relevant headers under overarching categories:
                if key in headings_dict:
                    cat = headings_dict[key]
                    val = re.sub(r"¶.+", "", val)
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
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", s)

def get_name_el(d, k):
    if k in d:
        if not "fulān" in d[k].lower() and not "none" in d[k].lower():
            return d[k]
    return ""


def extract_version_meta(uri, vers_yml_d, vers_yml_pth,
                         output_files_path, start_folder,
                         status_dic, incl_char_length,
                         remove_from_path=None, recalculate_lengths=True):
    """Extract the version-related metadata"""

    vers_uri = uri.build_uri("version")

    # - explicit primary version:
    primary_yml = False
    if "PRIMARY_VERSION" in vers_yml_d["90#VERS#ISSUES###:"]:
        primary_yml = True

    # - length in number of characters:
    recalc = False

    if recalculate_lengths:
        recalc = True
    
    length = vers_yml_d["00#VERS#LENGTH###:"].strip()
    # if length is not a number, recalculate:
    try:
        int(length) 
    except:
        recalc = True
    if length == "0":
        recalc = True
    
    char_length = ""
    if not length:
        recalc = True
    if incl_char_length:
        try:
            char_length = vers_yml_d["00#VERS#CLENGTH##:"].strip()
            int(char_length) # if char_length is not a number, recalculate
            if not char_length or char_length == "0":
                recalc = True
        except:
            recalc = True


    # recalculate the token length and character length if needed:
    if recalc:
        uri.extension = ""
        #pth = uri.build_pth(uri_type="version_file")
        pth = vers_yml_pth[:-4]
        for ext in [".mARkdown", ".completed", ".inProgress", ""]:
            version_fp = pth + ext
            if os.path.exists(version_fp):
                #if incl_char_length:
                #    char_length = ar_cnt_file(version_fp, mode="char")
                #    if str(char_length) == "0":
                #        char_length = count_elements(version_fp, mode="char")
                #    char_length = str(char_length)
                #    vers_yml_d["00#VERS#CLENGTH##:"] = char_length
                #length = ar_cnt_file(version_fp, mode="token")
                #if str(length) == "0":
                #    length = count_elements(version_fp, mode="tok")
                #length = str(length)
                #vers_yml_d["00#VERS#LENGTH###:"] = length
                if incl_char_length:
                    length, char_length = count_toks(version_fp, incl_chars=True)
                    char_length = str(char_length)
                    vers_yml_d["00#VERS#CLENGTH##:"] = char_length
                else:
                    length = count_toks(version_fp, incl_chars=False)
                length = str(length)
                vers_yml_d["00#VERS#LENGTH###:"] = length

                ymlS = dicToYML(vers_yml_d, reflow=False)
                with open(vers_yml_pth, mode="w", encoding="utf-8") as file:
                    file.write(ymlS)
                break

    # - edition information:
    ed_info = vers_yml_d["80#VERS#BASED####:"].strip()
    if ed_info.startswith("perma") or ed_info.upper().startswith("NO"):
        ed_info = []
    else:
        ed_info = re.split(r"[ \r\n¶]*[,;]+[ \r\n¶]*", ed_info)
    
    # - version tags (e.g., INCOMPLETE_TEXT, FOOTNOTES, ...):
    version_tags = re.findall(r"[A-Z_]{5,}",
                              vers_yml_d["90#VERS#ISSUES###:"])

    # - get the most advanced text file of this version
    #   (if different text files with the same extension exist in the folder)
    #   and give it a temporary secondary status:
    local_pth, status_score = give_status_score(vers_yml_pth, uri, length)

    # - build the link/path to the text file in the output file:
    fullTextURL = local_pth_to_fullTextURL(local_pth, start_folder,
                                           output_files_path,remove_from_path=remove_from_path)

    # - add the uri to the status_dic if the file is not missing:
    if os.path.exists(local_pth):
        book_uri = uri.build_uri("book")
        if book_uri not in status_dic:
            status_dic[book_uri] = []
        if primary_yml:
            status_indication = "pri##"
        else:
            status_indication = "%012d##" % int(status_score)
        status_dic[book_uri].append(status_indication + vers_uri)

    # tag all uncorrected OCR texts
    if "UNCORRECTED_OCR" in version_tags:
        uncorrected_OCR = True
    elif re.findall(r"\.EScr|Kraken|AOCP", vers_uri, flags=re.I):
        uncorrected_OCR = True
    else:
        uncorrected_OCR = False

    # gather all extracted metadata in a dictionary:
    vers_d = dict()
    vers_d["uri"] = vers_uri
    vers_d["id"] = uri.version
    vers_d["primary_yml"] = primary_yml
    vers_d["status"] = "sec"   # temporary status, will be changed later
    vers_d["tok_length"] = str(length)
    vers_d["char_length"] = str(char_length)
    vers_d["ed_info"] = ed_info
    vers_d["comment_tags"] = version_tags
    vers_d["local_pth"] = local_pth
    vers_d["fullTextURL"] = fullTextURL
    vers_d["uncorrected_OCR"] = uncorrected_OCR

    return vers_d, uri, status_dic


def extract_transcr_meta(uri, transcr_yml_d, transcr_yml_pth,
                         output_files_path, start_folder,
                         status_dic, incl_char_length,
                         remove_from_path=None, recalculate_lengths=True):
    """Extract transcription-related metadata"""

    transcr_uri = uri.build_uri("transcription")

    # - extract issues:
    excl_regex = r"(?i)^None$|^comma-separated list of issues"
    comment_tags = get_comma_sep_vals(
        transcr_yml_d, "90#TRNS#ISSUES###:",
        excl_regex=excl_regex, splitter=None, joiner=None)

    # - explicit primary version:
    primary_yml = False
    if "PRIMARY_VERSION" in comment_tags:
        primary_yml = True
    
    # - length in number of tokens and characters:
    recalc = False

    if recalculate_lengths:
        recalc = True

    length = transcr_yml_d["00#TRNS#LENGTH###:"].strip()
    # if length is not a number, recalculate:
    try:
        tok_length = str(int(length))
        if tok_length == "0":
            recalc = True
    except:
        tok_length = ""
        recalc = True
    if not length:
        recalc = True
    
    char_length = ""
    if incl_char_length:
        # if char_length is not a number, recalculate
        try:
            char_length = transcr_yml_d["00#TRNS#CLENGTH##:"].strip()
            char_length = str(int(char_length)) 
            if not char_length or char_length == 0:
                recalc = True
        except:
            char_length = ""
            recalc = True

    # recalculate the token length and character length if needed:
    if recalc:
        uri.extension = ""
        pth = transcr_yml_pth[:-4]
        for ext in [".mARkdown", ".completed", ".inProgress", ""]:
            transcr_fp = pth + ext
            if os.path.exists(transcr_fp):
                #if incl_char_length:
                #    char_length = ar_cnt_file(transcr_fp, mode="char")
                #    if str(char_length) == "0":
                #        char_length = count_elements(transcr_fp, mode="char")
                #    transcr_yml_d["00#TRNS#CLENGTH##:"] = str(char_length)

                #length = ar_cnt_file(transcr_fp, mode="token")
                #if str(length) == "0":
                #    length = count_elements(transcr_fp, mode="tok")
                #tok_length = str(length)
                #transcr_yml_d["00#TRNS#LENGTH###:"] = str(length)
                if incl_char_length:
                    length, char_length = count_toks(transcr_fp, incl_chars=True)
                    char_length = str(char_length)
                    transc_yml_d["00#TRNS#CLENGTH##:"] = char_length
                else:
                    length = count_toks(transcr_fp, incl_chars=False)
                tok_length = str(length)
                transcr_yml_d["00#TRNS#LENGTH###:"] = tok_length


                ymlS = dicToYML(transcr_yml_d, reflow=False)
                with open(transcr_yml_pth, mode="w", encoding="utf-8") as file:
                    file.write(ymlS)
                break

    # - edition information:
    key = "80#TRNS#BASED####:"
    excl_regex = r"(?i)^No$|^perma"
    ed_info = get_comma_sep_vals(transcr_yml_d, key, excl_regex=excl_regex,
                                 splitter=None, joiner=None)
    key = "80#TRNS#LINKS####:"

    excl_regex = r"(?i)^No$|SOURCE@permalink,"
    source = get_comma_sep_vals(transcr_yml_d, key, excl_regex=excl_regex,
                                 splitter=None, joiner=None)
    source = [s.split("@")[-1] for s in source if "SOURCE@" in s]

    # - get the most advanced text file of this version
    #   (if different text files with the same extension exist in the folder)
    #   and give it a temporary secondary status:
    local_pth, status_score = give_status_score(transcr_yml_pth, uri, length)

    # - build the link/path to the text file in the output file:
    fullTextURL = local_pth_to_fullTextURL(local_pth, start_folder, output_files_path,
                                           remove_from_path=remove_from_path)

    # - add the uri to the status_dic if the file is not missing:
    if os.path.exists(local_pth):
        manuscr_uri = uri.build_uri("manuscript")
        if manuscr_uri not in status_dic:
            status_dic[manuscr_uri] = []
        if primary_yml:
            status_indication = "pri##"
        else:
            status_indication = "%012d##" % int(status_score)
        status_dic[manuscr_uri].append(status_indication + transcr_uri)

    # tag all uncorrected OCR texts
    if "UNCORRECTED_OCR" in comment_tags:
        uncorrected_OCR = True
    elif re.findall(r"\.EScr|Kraken|AOCP", transcr_uri, flags=re.I):
        uncorrected_OCR = True
    else:
        uncorrected_OCR = False

    # gather all extracted metadata in a dictionary:
    transcr_d = dict()
    transcr_d["uri"] = transcr_uri
    transcr_d["id"] = uri.transcription
    transcr_d["comment_tags"] = comment_tags
    transcr_d["primary_yml"] = primary_yml
    transcr_d["tok_length"] = str(tok_length)
    transcr_d["char_length"] = str(char_length)
    transcr_d["ed_info"] = list(set(ed_info+source))
    transcr_d["status"] = "sec"   # temporary status, will be changed later
    transcr_d["local_pth"] = local_pth
    transcr_d["fullTextURL"] = fullTextURL
    transcr_d["uncorrected_OCR"] = uncorrected_OCR

    return transcr_d, uri, status_dic

def give_status_score(yml_pth, uri, length):
    """Select the text file with the most advanced extension for a specific version
    and define a score for it to later decide
    which version of a book should be the primary version"""
    #   The primary version of a book is the one that
    #   has the most developed annotation
    #   (signalled by the extension: mARkdown>completed>inProgress)
    #   If no version has an extension,
    #   the longest version will provisorally be considered primary.
    #   The length comparison can take place only after all versions
    #   have been documented.
    #   For this reason, versions with an extension
    #   are provisionally given a very high number
    #   in the status_dic instead of their real length,
    #   so that they will be chosen as primary version
    #   once the lengths are compared

    # - make a provisional (i.e., without extension)
    #   local filepath to the current version:
    uri.extension = ""
    local_pth = re.sub(r"\\", "/", yml_pth[:-4])
    
    if os.path.isfile(local_pth+".mARkdown"):
        status_score = 10000000000 + int(length)
        uri.extension = "mARkdown"
    elif os.path.isfile(local_pth+".completed"):
        status_score = 1000000000 + int(length)
        uri.extension = "completed"
    elif os.path.isfile(local_pth+".inProgress"):
        status_score = 100000000 + int(length)
        uri.extension = "inProgress"
    elif "Sham30K" in local_pth: # give Sham30K files lowest priority
        status_score = 0
        uri.extension = ""
    else:
        uri.extension = ""
        if length:
            status_score = int(length)
        else:
            status_score = 0

    # - rebuild the local_path, with the extension
    #   (in case there is more than one text file with the same ID
    #   but different extensions):
    if uri.extension:
        local_pth+= "." + uri.extension

    return local_pth, status_score

def local_pth_to_fullTextURL(local_pth, start_folder, output_files_path,
                             remove_from_path=None):
    if output_files_path:
        fullTextURL = re.sub(start_folder, output_files_path, local_pth)
    else:
        fullTextURL = local_pth
    if "githubusercontent" in fullTextURL:
        fullTextURL = re.sub(r"data/", "master/data/", fullTextURL)
    if remove_from_path:
        for folder in remove_from_path:
            fullTextURL = re.sub("/"+folder+"/", "/", fullTextURL)
    return fullTextURL

def get_language_key(d, key_template, language_codes):
    for lang in language_codes:
        k = key_template.format(lang)
        if k in d and d[k] and d[k].strip() != "" and d[k].strip().upper() != "NONE":
            return k

def get_first_lang_val(d, key_template, language_codes, sep=r"\s*,\s*",
                       excl_regex=r"(?i)^\s*None\s*$",
                       splitter=None, split_idx=-1, joiner=" :: ",
                       transcribe=False):
    """Get the first value from multilingual keys from a dictionary"""
    return get_multilingual_vals(d, key_template, language_codes, sep=sep,
                                 excl_regex=excl_regex, first_only=True,
                                 splitter=splitter, split_idx=split_idx,
                                 joiner=joiner, transcribe=transcribe)

def get_multilingual_vals(d, key_template, language_codes, sep=r"\s*,\s*",
                          excl_regex=r"(?i)^\s*None\s*$", first_only=False,
                          splitter=None, split_idx=-1, joiner=" :: ",
                          transcribe=False):
    """Get the values from multilingual keys from a dictionary

    Args:
        d (dict): the dictionary from which the values should be extracted
        key_template (str): key in which the language code is replaced with "{}"
        language_codes (list): language codes, to be plugged into the key_template
        sep (str): regex for the separator between sub-values. Defaults to comma
        excl_regex (str): regex pattern for values that should not be returned
            (e.g., default values, None values)
        first_only (bool): if True, return only the first value encountered
        splitter (str): if values consist of multiple parts separated by `splitter`,
            split the values on the splitter. If None: don't split.
        split_idx (int): which part of the split value should be retained.
            Defaults to -1 (the last part).
        joiner (str): separate the values by `joiner` in the output string;
            if None, return a list.

    Returns: str or list

    Examples:
        >>> d = {"10#LOC#INST#DE###:": "Staatsbibliothek zu Berlin"}
        >>> get_multilingual_vals(d, "10#LOC#INST#{}###:", ["EN", "DE"], excl_regex="^ *name of the")
        'Staatsbibliothek zu Berlin'
        >>> d = {"10#LOC#INST#DE###:": "Staatsbibliothek zu Berlin, Stabi Berlin"}
        >>> get_multilingual_vals(d, "10#LOC#INST#{}###:", ["EN", "DE"], excl_regex="^ *name of the")
        'Staatsbibliothek zu Berlin :: Stabi Berlin'
        >>> d = {"10#LOC#INST#DE###:": "Staatsbibliothek zu Berlin, Stabi Berlin", "10#LOC#INST#EN###:": "Berlin State Library"}
        >>> get_multilingual_vals(d, "10#LOC#INST#{}###:", ["EN", "DE"], excl_regex="^ *name of the")
        'Berlin State Library :: Staatsbibliothek zu Berlin :: Stabi Berlin'
        >>> d = {"10#LOC#INST#DE###:": "None"}
        >>> get_multilingual_vals(d, "10#LOC#INST#{}###:", ["EN", "DE"], excl_regex="^ *name of the")
        ''
        >>> d = {"10#LOC#INST#EN###:": "name of the institution, in English"}
        >>> get_multilingual_vals(d, "10#LOC#INST#{}###:", ["EN", "DE"], excl_regex="^ *name of the")
        ''
    """
    vals = []
    for lang in language_codes:
        k = key_template.format(lang)
        #if k in d and d[k] and d[k].strip() != "" and not re.findall(excl_regex, d[k]):
        #    if first_only:
        #        return d[k]
        #    vals.append(d[k])
        lang_vals = get_comma_sep_vals(d, k, sep=sep, excl_regex=excl_regex,
                                       splitter=splitter, split_idx=split_idx, joiner=None)
        if transcribe:
            lang_vals = [betaCodeToArSimple(v, lang_code=lang) for v in lang_vals]
        if first_only:
            return lang_vals[0]
        vals += lang_vals
    if joiner:
        return joiner.join(vals)
    else:
        return vals

def get_comma_sep_vals(d, key, sep=r"\s*,\s*", excl_regex=r"(?i)^\s*None\s*$",
                       splitter="@", split_idx=-1, joiner=" :: "):
    """Get the comma-separated values from a dictionary key.
    Returns an empty string if the value is a default value or None.

    Args:
        d (dict): the dictionary from which the values should be extracted
        key (str): dictionary key
        sep (str): regex for the separator between sub-values. Defaults to comma
        excl_regex (str): regex pattern for values that should not be returned
            (e.g., default values, None values)
        splitter (str): if values consist of multiple parts separated by `splitter`,
            split the values on the splitter. If None: don't split. Defaults to "@"
        split_idx (int): which part of the split value should be retained.
            Defaults to -1 (the last part).
        joiner (str): separate the values by `joiner` in the output string;
            if None, return a list.

    Returns: str or list
    
    Examples:
        >>> d = {"shelfmark": "Abc 123, Def 456"}
        >>> get_comma_sep_vals(d, "shelfmark", excl_regex=";shelfmark")
        'Abc 123 :: Def 456'
        >>> d = {"links": "SCAN@www.example.com"}
        >>> get_comma_sep_vals(d, "links")
        'www.example.com'
        >>> d = {"parts": "0255Jahiz.Hayawan@1A-28B, 0255Jahiz.Bukhala@29A-50B"}
        >>> get_comma_sep_vals(d, "parts", split_idx=0)
        '0255Jahiz.Hayawan :: 0255Jahiz.Bukhala'
        >>> d = {"shelfmark": "NONE"}
        >>> get_comma_sep_vals(d, "shelfmark")
        ''
        >>> d = {"shelfmark": "shelfmark; shelfmark"}
        >>> get_comma_sep_vals(d, "shelfmark", excl_regex=";shelfmark")
        ''
        
    """
    result_list = []
    vals = d.get(key, "").strip()
    if vals and not re.findall(excl_regex, vals):
        for val in re.split(sep, vals):
            val = val.strip()
            if val:
                if splitter:
                    result_list.append(re.split(splitter, val)[split_idx].strip())
                else:
                    result_list.append(val.strip())
    if joiner:
        return joiner.join(result_list)
    else:
        return result_list


def extract_location_meta(uri, loc_yml_d, all_loc_meta_d):
    """Extract location-related metadata"""

    loc_uri = uri.build_uri("location")

    # do not extract the metadata from the yml file
    # if it has already been extracted before
    # or if no readable YML file was found:

    if loc_uri in all_loc_meta_d:
        return all_loc_meta_d[loc_uri]

    if not loc_yml_d:
        return dict()

    key_template = "10#LOC#CITY#{}###:"
    excl_regex = r"(?i)^\s*None\s*$|name of the"
    city_lat = get_multilingual_vals(loc_yml_d, key_template,
                                      ["EN", "FR", "DE"], excl_regex=excl_regex)
    city_ar = get_multilingual_vals(loc_yml_d, key_template,
                                     ["AR", "FA", "UR"], excl_regex)

    key_template = "10#LOC#INST#{}###:"
    inst_lat = get_multilingual_vals(loc_yml_d, key_template, ["EN", "FR", "DE"])
    inst_ar = get_multilingual_vals(loc_yml_d, key_template, ["AR", "FA", "UR"])

    excl_regex = r"(?i)^\s*None\s*$|wikidata@id, src@id"
    external_id = get_comma_sep_vals(loc_yml_d, "70#LOC#EXTID#####:",
                                     excl_regex=excl_regex, splitter=None)

    # Add the extracted metadata to a dictionary:
    loc_d = dict()
    loc_d["uri"] = loc_uri
    loc_d["country"] = uri.country
    loc_d["city_lat"] = city_lat
    loc_d["city_ar"] = city_ar
    loc_d["institution_lat"] = inst_lat
    loc_d["institution_ar"] = inst_ar
    loc_d["external_id"] = external_id
    loc_d["manuscripts"] = []

    return loc_d


def extract_author_meta(uri, auth_yml_d, all_auth_meta_d, name_elements_d):
    """Extract author-related metadata"""

    auth_uri = uri.build_uri("author")

    # do not extract the book metadata from the yml file
    # if it has already been extracted before
    # or if no readable book YML file was found:

    if auth_uri in all_auth_meta_d:
        return all_auth_meta_d[auth_uri], name_elements_d

    if not auth_yml_d:
        return dict(), name_elements_d

    # - extract author's name:
    
    shuhra = ""
    full_name = ""
    author_lat = []
    author_ar = []

    # Add the latinized name from the URI:
    author_name_from_uri = insert_spaces(auth_uri)[4:]
    author_lat.append(author_name_from_uri)
    
    ## Get the author's shuhra:
    shuhra = auth_yml_d["10#AUTH#SHUHRA#AR:"].strip()
    if "Fulān" in shuhra or "none" in shuhra.lower():
        shuhra = ""
    if shuhra:
        shuhra = re.sub(r"[ \r\n¶]+", " ", shuhra).strip()
        author_lat.append(shuhra)
        author_ar.append(betaCodeToArSimple(shuhra))

    ## create a full (Latin-script) name from the name elements:
    
    name_comps = ["10#AUTH#LAQAB##AR:",
                  "10#AUTH#KUNYA##AR:",
                  "10#AUTH#ISM####AR:",
                  "10#AUTH#NASAB##AR:",
                  "10#AUTH#NISBA##AR:"]
    
    full_name = [auth_yml_d[x] for x in name_comps \
                 if x in auth_yml_d \
                 and not ("Fulān" in auth_yml_d[x] \
                          or "none" in auth_yml_d[x].lower())]
    full_name = " ".join(full_name)

    if full_name:
        full_name = re.sub(r"[ \r\n¶]+", " ", full_name).strip()
        author_lat.append(full_name)
        author_ar.append(betaCodeToArSimple(full_name))

    ## create a full English-language name from the name elements:
    
    name_comps_en = [x.replace("#AR:", "#EN:") for x in name_comps]
    english_name = [auth_yml_d[x] for x in name_comps_en \
                    if x in auth_yml_d and \
                    not ("Fulān" in auth_yml_d[x] \
                         or "none" in auth_yml_d[x].lower())]
    english_name = " ".join(english_name)
    if english_name.strip():
        author_lat.append(english_name)
      

    # collect author name elements in different languages/scripts:
    name_d = dict()
    for lang in ["AR", "EN", "FA"]:
        lang_d = dict()
        add = False
        for yml_k in ["10#AUTH#SHUHRA#AR:"]+name_comps:
            yml_k = yml_k.replace("#AR:", "#{}:".format(lang))
            k = re.findall(r"(?<=10#AUTH#)\w+", yml_k)[0].lower()
            lang_d[k] = get_name_el(auth_yml_d, yml_k)
            
            if lang_d[k]:
                add = True
        if add:
            if lang == "EN":
                name_d[lang] = lang_d
            else:
                # store a version of the name in transcription and Arabic script:
                name_d["LA"] = lang_d
                lang_d_converted = {k: betaCodeToArSimple(v) for k,v in lang_d.items()}
                name_d[lang] = lang_d_converted
                
    if name_d:
        name_elements_d[auth_uri] = name_d

    # - extract geo data related to author:
    geo = []
    auth_yml_fn = auth_uri + ".yml"
    geo_regex = r"\w+_RE(?:_\w+)?|\w+_[RSNO]\b|\w+XXXYYY\w*"
    
    born = re.findall(geo_regex, auth_yml_d["20#AUTH#BORN#####:"])
    for p in born:
        geo.append("born@"+p)
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(auth_yml_fn)    # SIDE_EFFECT!

        
    died = re.findall(geo_regex, auth_yml_d["20#AUTH#DIED#####:"])
    for p in died:
        geo.append("died@"+p)
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(auth_yml_fn)    # SIDE_EFFECT!
    
    resided = re.findall(geo_regex, auth_yml_d["20#AUTH#RESIDED##:"])
    for p in resided:
        geo.append("resided@"+p)
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(auth_yml_fn)    # SIDE_EFFECT!

    visited = re.findall(geo_regex, auth_yml_d["20#AUTH#VISITED##:"])
    for p in visited:
        geo.append("visited@"+p)
        if p not in geo_URIs:
            geo_URIs[p] = set()
        geo_URIs[p].add(auth_yml_fn)    # SIDE_EFFECT!

    excl_regex = r"(?i)^\s*None\s*$|viaf@id, wikidata@id, src@id"
    external_id = get_comma_sep_vals(auth_yml_d, "70#AUTH#EXTID####:",
                                     excl_regex=excl_regex, splitter=None)


    # Add the extracted metadata to a dictionary:
    author_d = dict()
    author_d["uri"] = auth_uri
    author_d["date"] = uri.date
    author_d["shuhra"] = shuhra
    author_d["full_name"] = full_name
    author_d["name_elements"] = name_d
    author_d["author_lat"] = author_lat
    author_d["author_ar"] = author_ar
    author_d["author_name_from_uri"] = author_name_from_uri
    author_d["vers_uri"] = english_name
    author_d["geo"] = geo
    author_d["external_id"] = external_id
    author_d["books"] = []

    return author_d, name_elements_d


def extract_manuscr_meta(uri, manuscr_yml_d, tags_dic, all_manuscr_meta_d):
    """Extract manuscript-related metadata"""
    manuscr_uri = uri.build_uri("manuscript")

    # do not extract the metadata from the yml file
    # if it has already been extracted before
    # or if no readable YML file was found:
    
    if manuscr_uri in all_manuscr_meta_d:
        return all_manuscr_meta_d[manuscr_uri]
    
    if not manuscr_yml_d:
        return dict()

    # - extract shelfmark(s):
    excl_regex = r"(?i)^None$|shelfmark;"
    shelfmark = get_comma_sep_vals(
        manuscr_yml_d, "10#MS#SHELFM#####:", sep=" *; *",
        excl_regex=excl_regex, splitter=None)

    # - extract genre metadata:
    key_template = "10#MS#GENRES#####:"
    excl_regex = r"(?i)^\s*None\s*$|^\s?src@keyword"
    genres = get_comma_sep_vals(
        manuscr_yml_d, key_template,
        excl_regex=excl_regex, splitter=None, joiner=None)

    # - extract title metadata:
    key_template = "10#MS#TITLE#{}###:"
    excl_regex = r"(?i)^\s*None\s*$|title\(s\)"
    language_codes = ["EN", "FR", "DE"]
    titles_lat = get_multilingual_vals(manuscr_yml_d, key_template,
                                                language_codes, excl_regex=excl_regex)
    language_codes = ["AR", "FA", "UR"]
    titles_ar = get_multilingual_vals(manuscr_yml_d, key_template,
                                                language_codes, excl_regex=excl_regex)

    # - extract author metadata:
    key_template = "10#MS#AUTHOR#{}##:"
    excl_regex = r"(?i)^\s*None\s*$|author\(s\)"
    language_codes = ["EN", "FR", "DE"]
    authors_lat = get_multilingual_vals(manuscr_yml_d, key_template,
                                                 language_codes, excl_regex=excl_regex)
    language_codes = ["AR", "FA", "UR"]
    authors_ar = get_multilingual_vals(manuscr_yml_d, key_template,
                                                language_codes, excl_regex=excl_regex)

    # - extract part URIs:
    excl_regex = r"(?i)^None$|URI@page_range, URI@page_range"
    parts = get_comma_sep_vals(
        manuscr_yml_d, "40#MS#PARTS######:",
        excl_regex=excl_regex, splitter=None, joiner=None)

    # - extract external ID:
    excl_regex = r"(?i)^\s*None\s*$|wikidata@id, src@id"
    external_id = get_comma_sep_vals(manuscr_yml_d, "70#MS#EXTID######:",
                                                  excl_regex=excl_regex, splitter=None)

    # - extract catalog reference:
    excl_regex = r"(?i)^None$|^ *reference to a manuscript catalogue *$"
    catalog_ref = get_comma_sep_vals(
        manuscr_yml_d, "80#MS#CATREF#####:",
        excl_regex=excl_regex, splitter=None)

    # - extract links:
    excl_regex = r"(?i)^None$|^ *SOURCE@permalink, IIIF@permalink"
    links = get_comma_sep_vals(
        manuscr_yml_d, "80#MS#LINKS######:",
        excl_regex=excl_regex, splitter=None)

    # - extract issues:
    excl_regex = r"(?i)^None$|^ *comma-separated list of issues"
    issues = get_comma_sep_vals(
        manuscr_yml_d, "90#MS#ISSUES#####:",
        excl_regex=excl_regex, splitter=None, joiner=None)

    # Add the extracted metadata to a dictionary:
    manuscr_d = dict()
    manuscr_d["uri"] = manuscr_uri
    manuscr_d["shelfmark"] = shelfmark
    manuscr_d["genre_tags"] = genres
    manuscr_d["titles_lat"] = titles_lat
    manuscr_d["titles_ar"] = titles_ar
    manuscr_d["authors_lat"] = authors_lat
    manuscr_d["authors_ar"] = authors_ar
    manuscr_d["parts"] = parts
    manuscr_d["external_id"] = external_id
    manuscr_d["catalog_ref"] = catalog_ref
    manuscr_d["links"] = links
    manuscr_d["issues"] = issues
    manuscr_d["transcriptions"] = []

    return manuscr_d


def extract_book_meta(uri, book_yml_d, tags_dic, all_book_meta_d, book_rel_d):
    """Extract book-related metadata"""
    
    book_uri = uri.build_uri("book")

    # do not extract the book metadata from the yml file
    # if it has already been extracted before
    # or if no readable book YML file was found:
    
    if book_uri in all_book_meta_d:
        return all_book_meta_d[book_uri], book_rel_d
    if not book_yml_d:
        return dict(), book_rel_d

    # - extract book relations:
    
    if "40#BOOK#RELATED##:" in book_yml_d:
        rels = book_yml_d["40#BOOK#RELATED##:"].strip()
        if rels.startswith("URI of"):
            rels = ""
        rels = re.sub(r"[ \r\n¶]+", " ", rels)
        rels = re.split(r" *[;:]+ *", rels)
        rels = [rel for rel in rels if rel.strip()]
        for rel in rels:
            if "@" in rel:  # new format: COMM.sharh@0255Jahiz.Hayawan
                rel_types = rel.strip().split("@")[0]
                rel_book = rel.strip().split("@")[1]
            else:           # old format: 0255Jahiz.Hayawan (COMM.sharh)
                try:
                    rel_types = re.findall(r"\(([^\)]+)", rel)[0].strip()
                except:
                    print(book_uri, ":")
                    print("    no relationship type found in ", [rel])
                    continue
                rel_book = re.sub(r" *\(.+", "", rel).strip()
            
            
            if not book_uri in book_rel_d:
                book_rel_d[book_uri] = []
            if not rel_book in book_rel_d:
                book_rel_d[rel_book] = []
            for rel_type in re.split(r" *, *", rel_types):
                if "." in rel_type:
                    main_rel_type = re.split(r" *\. *", rel_type)[0]
                    sec_rel_type = re.split(r" *\. *", rel_type)[1]
                else:
                    main_rel_type = rel_type
                    sec_rel_type = ""
                rel = {"source": book_uri,
                       "main_rel_type": main_rel_type,
                       "sec_rel_type": sec_rel_type,
                       "dest": rel_book}
                if not rel in  book_rel_d[book_uri]:
                    book_rel_d[book_uri].append(rel)
                if not rel in book_rel_d[rel_book]:
                    book_rel_d[rel_book].append(rel)
        

    # - extract title metadata:

    title_lat = []
    title_ar = []
    if book_yml_d:
        for c in ["10#BOOK#TITLEA#AR:", "10#BOOK#TITLEB#AR:"]:
            if not ("al-Muʾallif" in book_yml_d[c]\
                    or "none" in book_yml_d[c].lower()):
                title_lat.append(book_yml_d[c].strip())
                title_ar.append(betaCodeToArSimple(title_lat[-1]))

    if not title_lat:
        title_lat.append(insert_spaces(uri.title))

    # - extract genre tags:

    genre_tags = book_yml_d["10#BOOK#GENRES###:"].strip()
    if genre_tags.startswith("src"):
        genre_tags = []
    if genre_tags:
        genre_tags = re.split(r" *[;:,]+ *", genre_tags)

    # - add genre tags from Maxim's tag file:
    
    if uri.version in tags_dic:
        genre_tags += tags_dic[uri.version]

    # - get external IDs:
    excl_regex = r"(?i)^\s*None\s*$|viaf@id, wikidata@id, src@id"
    external_id = get_comma_sep_vals(book_yml_d, "70#BOOK#EXTID####:",
                                     excl_regex=excl_regex, splitter=None)

    # Add the extracted metadata to a dictionary:
    book_d = dict()
    book_d["uri"] = book_uri
    book_d["title_ar"] = title_ar
    book_d["title_lat"] = title_lat
    book_d["genre_tags"] = list(set(genre_tags))
    book_d["external_id"] = external_id
    book_d["versions"] = []
    book_d["relations"] = []

    return book_d, book_rel_d

def load_yml(yml_pth):
    try:
        yml_d = readYML(yml_pth)
        if not yml_d:
            yml_d = fix_broken_yml(yml_pth)
    except:
        print("YML file not found:", yml_pth)
        yml_d = {}
    return yml_d

def list2str(arr, sep=" :: "):
    """Turn a list into a string (removing empty elements and using a specified separator between elements)"""
    if type(arr) == str:
        return arr
    return sep.join([str(el) for el in arr if str(el).strip()])

def aggregate_arabic_names(all_vers_meta_d, all_book_meta_d, all_auth_meta_d,
                           all_transcr_meta_d, all_manuscr_meta_d, all_loc_meta_d):
    # if no Arabic author name is provided in the author yml file,
    # aggregate the Arabic names found in all text files by the author:
    for auth_uri, auth_d in all_auth_meta_d.items():
        if not auth_d["author_ar"]:
            for book_uri in auth_d["books"]:
                book_d = all_book_meta_d[book_uri]
                for vers_uri in book_d["versions"]:
                    vers_d = all_vers_meta_d[vers_uri]
                    if "author_ar" in vers_d and vers_d["author_ar"]:
                        for name in vers_d["author_ar"]:
                            if name not in auth_d["author_ar"]:
                                auth_d["author_ar"].append(name)

    # if no Arabic book title is provided in the book yml file,
    # aggregate the Arabic book titles found in all text files of the book:
    for book_uri, book_d in all_book_meta_d.items():
        if "title_ar" in book_d and not book_d["title_ar"]:
            for vers_uri in book_d["versions"]:
                vers_d = all_vers_meta_d[vers_uri]
                if "title_ar" in vers_d and vers_d["title_ar"]:
                    for title in vers_d["title_ar"]:
                        if title not in book_d["title_ar"]:
                            book_d["title_ar"].append(title)

    # if no Arabic author is provided in the manuscript yml file,
    # check if its URI exists in the author metadata:
    # TO DO

    # if no Arabic title is provided in the manuscript yml file,
    # check if its URI exists in the book metadata:
    # TO DO


    return all_vers_meta_d, all_book_meta_d, all_auth_meta_d, all_transcr_meta_d, all_manuscr_meta_d, all_loc_meta_d

    
        

def create_tsv_row(vers_uri, all_vers_meta_d, all_book_meta_d, all_auth_meta_d,
                   split_ar_lat=True, incl_char_length=True, sep="\t"):
    # get the relevant dictionaries:
    
    vers_d = all_vers_meta_d[vers_uri]
    uri = URI(vers_d["fullTextURL"])
    book_uri = uri.build_uri("book")
    book_d = all_book_meta_d[book_uri]
    auth_uri = uri.build_uri("author")
    auth_d = all_auth_meta_d[auth_uri]

    # prepare values for the tsv row:
    
    author_ar = list2str(auth_d["author_ar"])
    if not author_ar and "author_ar" in vers_d:
        author_ar = list2str(vers_d["author_ar"])
    author_lat = list2str(auth_d["author_lat"])
    
    title_ar = list2str(book_d["title_ar"])
    if not title_ar and "title_ar" in vers_d:
        title_ar = list2str(vers_d["title_ar"])
    title_lat = list2str(book_d["title_lat"])
    
    ed_info = list2str(vers_d["ed_info"])
    
    tags = book_d["genre_tags"] + auth_d["geo"] + vers_d["comment_tags"]
    if uri.extension:
        tags.append(uri.extension.upper())
    tags = list2str(tags)
    
    language = uri.language
    subcorpus = language
    uncorrected_OCR = vers_d["uncorrected_OCR"]

    # build the tsv row:
    
    if not split_ar_lat:
        author = list2str([author_lat, author_ar])
        title = list2str([title_lat, title_ar])
        city = ""
        institution = ""
    else:
        author = author_ar + sep + author_lat
        title = title_ar + sep + title_lat
        city = "" + sep + ""
        institution = "" + sep + ""

    if incl_char_length:
        length = vers_d["tok_length"] + sep + vers_d["char_length"]
    else:
        length = vers_d["tok_length"]

    shelfmark = ""
    catalog_ref = ""
    parts = ""
    row = [vers_uri, language, subcorpus, uncorrected_OCR, auth_d["date"], author,
           book_uri, title, ed_info, uri.version, vers_d["status"],
           length, vers_d["fullTextURL"],
           tags, auth_d["author_name_from_uri"],
           auth_d["shuhra"], auth_d["full_name"],
           city, institution, shelfmark, catalog_ref, parts]
    #if incl_char_length:
    #    row.append(vers_d["char_length"])

    return sep.join([str(cell) for cell in row])

def create_transcr_tsv_row(transcr_uri, all_transcr_meta_d, all_manuscr_meta_d,
                           all_loc_meta_d, split_ar_lat=True, incl_char_length=True, sep="\t"):
    # get the relevant dictionaries:
    
    transcr_d = all_transcr_meta_d[transcr_uri]
    uri = URI(transcr_d["fullTextURL"])

    language= ",".join(uri.languages.keys())
    
    manuscr_uri = uri.build_uri("manuscript")
    manuscr_d = all_manuscr_meta_d[manuscr_uri]
    loc_uri = uri.build_uri("location")
    loc_d = all_loc_meta_d[loc_uri]

    # prepare values for the tsv row:
    author_ar = list2str(manuscr_d["authors_ar"])
    if not author_ar and "author_ar" in transcr_d:
        author_ar = list2str(transcr_d["author_ar"])
    author_lat = manuscr_d["authors_lat"]
    if not author_lat:
        author_lat = author_ar
    author_ar = betaCodeToArSimple(author_ar)
    
    title_ar = list2str(manuscr_d["titles_ar"])
    if not title_ar and "title_ar" in transcr_d:
        title_ar = list2str(transcr_d["title_ar"])
    title_lat = list2str(manuscr_d["titles_lat"])
    if not title_lat:
        title_lat = title_ar
    title_ar = betaCodeToArSimple(title_ar)

    catalog_ref = manuscr_d["catalog_ref"]
    
    ed_info = list2str(transcr_d["ed_info"])    
    tags = manuscr_d["genre_tags"] + manuscr_d["issues"] + transcr_d["comment_tags"]
    if uri.extension:
        tags.append(uri.extension.upper())
    tags = list2str(tags)

    city_lat = loc_d["city_lat"]
    city_ar = betaCodeToArSimple(loc_d["city_ar"])
    institution_lat = loc_d["institution_lat"]
    institution_ar = betaCodeToArSimple(loc_d["institution_ar"])
    shelfmark = manuscr_d["shelfmark"]
    parts = list2str(manuscr_d["parts"])
    uncorrected_OCR = transcr_d["uncorrected_OCR"]

    book_uris = []
    for p in manuscr_d["parts"]:
        book_uri = p.split("@")[0]
        try:
            if URI(book_uri).uri_type == "book":
                book_uris.append(book_uri)
        except:
            continue
    book_uri = " :: ".join(book_uris)

    # build the tsv row:
    
    if not split_ar_lat:
        author = list2str([author_lat, author_ar])
        title = list2str([title_lat, title_ar])
        city = list2str([city_lat, city_ar])
        institution = list2str([institution_lat, institution_ar])
    else:
        author = author_ar + sep + author_lat
        title = title_ar + sep + title_lat
        city = city_ar + sep + city_lat
        institution = institution_ar + sep + institution_lat

    if incl_char_length:
        length = transcr_d["tok_length"] + sep + transcr_d["char_length"]
    else:
        length = transcr_d["tok_length"]
    
    date = ""
    author_from_uri = ""
    
    
    
    author_shuhra = sorted(author_lat.split(" :: "), key=lambda el: len(el))[0]
    author_full_name = sorted(author_lat.split(" :: "), key=lambda el: len(el))[-1]
    subcorpus = "MSS"
              
    row = [transcr_uri, language, subcorpus, uncorrected_OCR, date, author,
           book_uri, title, ed_info, uri.transcription, transcr_d["status"],
           length, transcr_d["fullTextURL"],
           tags, author_from_uri,
           author_shuhra, author_full_name,
           city, institution, shelfmark, catalog_ref, parts]
    #if incl_char_length:
    #    row.append(transcr_d["char_length"])

    return sep.join([str(cell) for cell in row])

def collectMetadata(start_folder, exclude, csv_outpth, yml_outpth,
                    book_rel_outpth, name_el_outpth,
                    incl_char_length=False, split_ar_lat=False,
                    flat_folder=False, output_files_path=None,
                    remove_from_path=None):
    """Collect the metadata from URIs, YML files and text file headers
    and save the metadata in csv and yml files.

    Args:
        start_folder (str): path to the parent folder of all folders
            from which metadata should be collected
        exclude (list): list of directory names that should be excluded
            from the metadata collections
        csv_outpth (str): path to the output csv file
        yml_outpth (str): path to the output yml file
        incl_char_length (bool): if True, a column for character length
            will be included in the metadata
        split_ar_lat (bool): if True, Arabic and transliterated data on
            title and author will be put into separate columns
        remove_from_path (list): remove the folders in this list from the path
    """

    dataYML = []
    dataCSV = {}  
    status_dic = {}
    split_files = dict()
    start_folder = re.sub(r"\\\\", "/", start_folder)
    book_rel_d = dict()
    name_elements_d = dict()
    all_auth_meta_d = dict()    # will contain all author-level metadata
    all_book_meta_d = dict()    # will contain all book-level metadata
    all_vers_meta_d = dict()    # will contain all version-level metadata
    all_loc_meta_d = dict()     # will contain all location-level metadata
    all_manuscr_meta_d = dict() # will contain all manuscript-level metadata
    all_transcr_meta_d = dict() # will contain all transcription-level metadata

    version_yml_regex = r"^\d{4}[A-Za-z]+\.[A-Za-z\d]+\.\w+-[a-z]{3}\d+\.yml$"
    transcr_yml_regex = r"^MS\d{4}[A-Za-z]+\.[A-Za-z\d_]+\.\w+-(?:[a-z]{3}\d+)+\.yml$"
    for root, dirs, files in os.walk(start_folder):
        dirs[:] = [d for d in sorted(dirs) if d not in exclude]
        
        for fn in files:
            # select only the version yml files:
            if re.search(version_yml_regex, fn):
                # build the relevant URIs:
                uri = URI(os.path.join(root, fn))
                vers_uri = uri.build_uri("version")
                book_uri = uri.build_uri("book")
                auth_uri = uri.build_uri("author")

                # add the version ID to the version_ids dictionary
                # to check for duplicate IDs later:
                if not uri.version in version_ids:
                    version_ids[uri.version] = []
                version_ids[uri.version].append(fn)

                # build the filepaths to all yml files related
                # to the current version yml file:
                if not flat_folder:
                    auth_folder = os.path.dirname(root)
                else:
                    auth_folder = root
                vers_yml_pth = os.path.join(root, fn)
                book_yml_pth = os.path.join(root, uri.build_uri(uri_type="book")+".yml")
                auth_yml_pth = os.path.join(auth_folder, uri.build_uri(uri_type="author")+".yml")

                # bring together all yml data related to the current version
                # and store in the master dataYML variable:
                vers_yml_d = load_yml(vers_yml_pth)
                book_yml_d = load_yml(book_yml_pth)
                auth_yml_d = load_yml(auth_yml_pth)

                record = "{}\n{}\n{}\n{}\n".format(
                    splitter,
                    dicToYML(vers_yml_d, reflow=False),
                    dicToYML(book_yml_d, reflow=False),
                    dicToYML(auth_yml_d, reflow=False))
                dataYML.append(record)

                # 1. collect the metadata related to the current version:

                ## A) from the author YML file:

                auth_d, name_elements_d = extract_author_meta(uri, auth_yml_d, all_auth_meta_d,
                                                              name_elements_d)
                if book_uri not in auth_d["books"]:
                    auth_d["books"].append(book_uri)

                ## B) from the book yml file:

                book_d, book_rel_d = extract_book_meta(uri, book_yml_d, tags_dic,
                                                       all_book_meta_d, book_rel_d)
                book_d["versions"].append(vers_uri)

                ## C) from the version YML file:

                vers_d, uri, status_dic = extract_version_meta(uri, vers_yml_d, vers_yml_pth,
                                                               output_files_path, start_folder,
                                                               status_dic, incl_char_length,
                                                               remove_from_path=remove_from_path)

                # 2. collect additional metadata (mostly in Arabic!)
                #    from the text file headers:

                local_pth = vers_d["local_pth"]
                if not os.path.exists(local_pth):
                    print("MISSING FILE? {} does not exist".format(local_pth))
                else:
                    header_meta = extract_metadata_from_header(local_pth)

                    # - author name:

                    #if not auth_d["author_ar"]: # if no Arabic author name was found in YML file:
                    #    auth_d["author_ar"] = list(set(header_meta["AuthorName"]))
                    vers_d["author_ar"] = list(set(header_meta["AuthorName"]))

                    # - book title:
                    
                    #if not book_d["title_ar"]: # if no title was found in the YML file
                    #    book_d["title_ar"] += list(set(header_meta["Title"]))
                    vers_d["title_ar"] = list(set(header_meta["Title"]))

                    # - information about the current version's edition:
                    
                    ed_info = header_meta["Edition:Editor"] +\
                              header_meta["Edition:Place"] +\
                              header_meta["Edition:Date"] +\
                              header_meta["Edition:Publisher"]
                    vers_d["ed_info"] += ed_info

                    # - additional genre tags:
                    
                    coll_id = re.findall(r"[A-Za-z]+", uri.version)[0]
                    for el in header_meta["Genre"]:
                        for t in el.split(" :: "):
                            if coll_id+"@"+t not in book_d["genre_tags"]:
                                book_d["genre_tags"].append(coll_id+"@"+t)


                # Deal with files split into multiple parts because
                # they were too large: 
                if re.search(r"[A-Z]-", vers_uri):
                    print("FILE SPLIT because it was too big:", vers_uri)
                    m = re.sub(r"[A-Z]-", "-", vers_uri)
                    if m not in split_files:
                        split_files[m] = []
                    split_files[m].append(vers_uri)

                # Add the extracted metadata to the relevant aggregating dictionaries:
                all_auth_meta_d[auth_uri] = auth_d
                all_book_meta_d[book_uri] = book_d
                all_vers_meta_d[vers_uri] = vers_d


            elif re.search(transcr_yml_regex, fn):
                # build the relevant URIs:
                uri = URI(os.path.join(root, fn))
                transcr_uri = uri.build_uri("transcription")
                manuscr_uri = uri.build_uri("manuscript")
                loc_uri = uri.build_uri("location")

                # add the version ID to the version_ids dictionary
                # to check for duplicate IDs later:
                if not uri.transcription in version_ids:
                    version_ids[uri.transcription] = []
                version_ids[uri.transcription].append(fn)

                # build the filepaths to all yml files related
                # to the current version yml file:
                if not flat_folder:
                    loc_folder = os.path.dirname(root)
                else:
                    loc_folder = root
                transcr_yml_pth = os.path.join(root, fn)
                manuscr_yml_pth = os.path.join(root, uri.build_uri(uri_type="manuscript")+".yml")
                loc_yml_pth = os.path.join(loc_folder, uri.build_uri(uri_type="location")+".yml")

                # bring together all yml data related to the current version
                # and store in the master dataYML variable:
                transcr_yml_d = load_yml(transcr_yml_pth)
                manuscr_yml_d = load_yml(manuscr_yml_pth)
                loc_yml_d = load_yml(loc_yml_pth)

                record = "{}\n{}\n{}\n{}\n".format(splitter,
                                                   dicToYML(transcr_yml_d, reflow=False),
                                                   dicToYML(manuscr_yml_d, reflow=False),
                                                   dicToYML(loc_yml_d, reflow=False)
                                                   )
                dataYML.append(record)

                # 1. collect the metadata related to the current version:

                ## A) from the location YML file:

                loc_d = extract_location_meta(uri, loc_yml_d, all_loc_meta_d)
                
                if manuscr_uri not in loc_d["manuscripts"]:
                    loc_d["manuscripts"].append(manuscr_uri)

                ## B) from the manuscript yml file:

                manuscr_d = extract_manuscr_meta(uri, manuscr_yml_d, tags_dic,
                                                 all_manuscr_meta_d)
                manuscr_d["transcriptions"].append(transcr_uri)

                ## C) from the transcription YML file:

                transcr_d, uri, status_dic = extract_transcr_meta(
                    uri, transcr_yml_d, transcr_yml_pth, output_files_path, 
                    start_folder, status_dic, incl_char_length,
                    remove_from_path=remove_from_path)

                # 2. collect additional metadata (mostly in Arabic!)
                #    from the text file headers:

                local_pth = transcr_d["local_pth"]
                if not os.path.exists(local_pth):
                    print("MISSING FILE? {} does not exist".format(local_pth))
                else:
                    header_meta = extract_metadata_from_header(local_pth)

                    # - author name:

                    transcr_d["author_ar"] = list(set(header_meta["AuthorName"]))

                    # - book title:
                    
                    transcr_d["title_ar"] = list(set(header_meta["Title"]))

                    # - information about the current version's edition:
                    
                    ed_info = header_meta["Edition:Editor"] +\
                              header_meta["Edition:Place"] +\
                              header_meta["Edition:Date"] +\
                              header_meta["Edition:Publisher"]
                    transcr_d["ed_info"] += ed_info

                    # - additional genre tags:
                    
                    coll_id = re.findall("[A-Za-z]+", uri.transcription)[0]
                    for el in header_meta["Genre"]:
                        for t in el.split(" :: "):
                            if coll_id+"@"+t not in manuscr_d["genre_tags"]:
                                manuscr_d["genre_tags"].append(coll_id+"@"+t)


                # Add the extracted metadata to the relevant aggregating dictionaries:
                all_loc_meta_d[loc_uri] = loc_d
                all_manuscr_meta_d[manuscr_uri] = manuscr_d
                all_transcr_meta_d[transcr_uri] = transcr_d

    # define which text file(s) get primary status:
    for book_or_manuscr_uri, versions in status_dic.items():
        versions = sorted(versions, reverse=True)
        # give primary status to all text files that have "PRIMARY_VERSION" in version yml file:
        if versions[0].startswith("pri"): 
            primary = [x for x in versions if x.startswith("pri")]
            for x in primary:
                pri_uri = x.split("##")[1]
                if pri_uri.startswith("MS"):
                    all_transcr_meta_d[pri_uri]["status"] = "pri"
                else:
                    all_vers_meta_d[pri_uri]["status"] = "pri"
        # If no yml file has "PRIMARY_VERSION", give primary status to "longest" version:
        else:
            pri_uri = versions[0].split("##")[1]
            if pri_uri.startswith("MS"):
                all_transcr_meta_d[pri_uri]["status"] = "pri"
            else:
                all_vers_meta_d[pri_uri]["status"] = "pri"

    # Write a json file containing all texts that have been split
    # into parts because they were too big (URIs with VolsA, VolsB, ...):
    split_files_fp = re.sub(r"metadata_light.csv", "split_files.json", csv_outpth)
    with open(split_files_fp, mode='w', encoding='utf-8') as outfile:
        json.dump(split_files, outfile, indent=4)  

    # add compound data for text files split because of their size:
    all_vers_meta_d = add_split_files_meta(split_files, all_vers_meta_d, incl_char_length)

    # save metadata to tsv:
    save_as_tsv(all_vers_meta_d, all_book_meta_d, all_auth_meta_d,
                all_transcr_meta_d, all_manuscr_meta_d, all_loc_meta_d,
                csv_outpth, split_ar_lat=split_ar_lat,
                incl_char_length=incl_char_length)

    # save the combined yml data in a master yml file: 
    with open(yml_outpth, "w", encoding="utf8") as outfile:
        outfile.write("\n".join(dataYML))

    # save the name elements to a json file:
    with open(name_el_outpth, mode="w", encoding="utf-8") as outfile:
        json.dump(name_elements_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)

    # save the book relations:
    with open(book_rel_outpth, "w", encoding="utf-8") as outfile:
        json.dump(book_rel_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)

    # store the book relations in the all_book_meta_d:
    for book_uri in book_rel_d:
        try:
            all_book_meta_d[book_uri]["relations"] = book_rel_d[book_uri]
        except:
            all_book_meta_d[book_uri] = dict()
            all_book_meta_d[book_uri]["relations"] = book_rel_d[book_uri]

    # aggregate Arabic author and title names from metadata headers
    # if none are given in the yml files:

    r = aggregate_arabic_names(all_vers_meta_d, all_book_meta_d, all_auth_meta_d,
                               all_transcr_meta_d, all_manuscr_meta_d, all_loc_meta_d)
    [all_vers_meta_d, all_book_meta_d, all_auth_meta_d, all_transcr_meta_d, all_manuscr_meta_d, all_loc_meta_d] = r

    # store all version, book and author metadata in json files:
    book_fp = re.sub(r"metadata_light.csv", "all_book_meta.json", csv_outpth)
    with open(book_fp, mode="w", encoding="utf-8") as outfile:
        json.dump(all_book_meta_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)

    auth_fp = re.sub(r"metadata_light.csv", "all_author_meta.json", csv_outpth)
    with open(auth_fp, mode="w", encoding="utf-8") as outfile:
        json.dump(all_auth_meta_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)

    vers_fp = re.sub(r"metadata_light.csv", "all_version_meta.json", csv_outpth)
    with open(vers_fp, mode="w", encoding="utf-8") as outfile:
        json.dump(all_vers_meta_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)

    # store all transcription, manuscript and location metadata in json files:
    manuscr_fp = re.sub(r"metadata_light.csv", "all_manuscript_meta.json", csv_outpth)
    with open(manuscr_fp, mode="w", encoding="utf-8") as outfile:
        json.dump(all_manuscr_meta_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)

    loc_fp = re.sub(r"metadata_light.csv", "all_location_meta.json", csv_outpth)
    with open(loc_fp, mode="w", encoding="utf-8") as outfile:
        json.dump(all_loc_meta_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)

    transcr_fp = re.sub(r"metadata_light.csv", "all_transcription_meta.json", csv_outpth)
    with open(transcr_fp, mode="w", encoding="utf-8") as outfile:
        json.dump(all_transcr_meta_d, outfile, indent=2, ensure_ascii=False, sort_keys=True)


def add_split_files_meta(split_files, all_vers_meta_d, incl_char_length):
    # add data for files split into multiple parts:
    
    for file in split_files:
        # make sure each part has the same status:
        statuses = [all_vers_meta_d[part]["status"] for part in split_files[file]]
        for part in split_files[file]:
            if "pri" in statuses:
                all_vers_meta_d[part]["status"] = "pri"

        # aggregate the length of the parts:
        file_length = 0
        file_clength = 0
        for part in split_files[file]:
            file_length += int(all_vers_meta_d[part]["tok_length"])
            if incl_char_length:
                file_clength += int(all_vers_meta_d[part]["char_length"])
                
        # add an extra line to the csv data with metadata of the compound file:
        first_part = split_files[file][0]
        vers_d = copy.deepcopy(all_vers_meta_d[first_part])
        vers_d["versionUri"] = file
        vers_d["id"] = vers_d["id"][:-1] # drop the letter
        vers_d["status"] = "sec"  # give the compound text secondary status so that it is not selected for passim etc.
        vers_d["tok_length"] = file_length
        vers_d["fullTextURL"] = re.sub(r"[A-Z](-[a-z]{3}\d)", r"\1", vers_d["fullTextURL"])
        if incl_char_length:
            vers_d["char_length"] = file_clength
        all_vers_meta_d[file] = vers_d

    return all_vers_meta_d

def save_as_tsv(all_vers_meta_d, all_book_meta_d, all_auth_meta_d,
                all_transcr_meta_d, all_manuscr_meta_d, all_loc_meta_d,
                csv_outpth, split_ar_lat, incl_char_length, sep="\t"):

    # define the tsv file header:
    if not split_ar_lat:
        author = "author"
        title = "title"
        author_shuhra = "author_shuhra"
        author_full_name = "author_full_name"
        city = "city"
        institution = "institution"
    else:
        author = "author_ar" + sep + "author_lat"
        title = "title_ar" + sep + "title_lat"
        author_shuhra = "author_lat_shuhra"
        author_full_name = "author_lat_full_name"
        city = "city_ar" + sep + "city_lat"
        institution = "institution_ar" + sep +"institution_lat"
    if incl_char_length:
        length = "tok_length" + sep + "char_length"
    else:
        length = "tok_length"
    header = ["versionUri", "language", "subcorpus", "uncorrected_OCR", "date", author, "book",
              title, "ed_info", "id", "status",
              length, "url",
              "tags", "author_from_uri", author_shuhra, author_full_name,
              city, institution, "shelfmark", "catalog_ref", "parts"]
    
    header = sep.join(header)

    tsv = [header, ]

    print("="*80)
    print("COLLECTING INTO A CSV FILE ({} LINES)...".format(len(all_vers_meta_d)))
    print("="*80)

    for vers_uri in sorted(all_vers_meta_d.keys()):
        row = create_tsv_row(vers_uri, all_vers_meta_d,
                             all_book_meta_d, all_auth_meta_d,
                             split_ar_lat=split_ar_lat,
                             incl_char_length=incl_char_length)
        tsv.append(row)
    for transcr_uri in sorted(all_transcr_meta_d.keys()):
        row = create_transcr_tsv_row(transcr_uri, all_transcr_meta_d,
                             all_manuscr_meta_d, all_loc_meta_d,
                             split_ar_lat=split_ar_lat,
                             incl_char_length=incl_char_length)
        tsv.append(row)

    # save csv file:
    with open(csv_outpth, "w", encoding="utf8") as outfile:
        outfile.write("\n".join(tsv))


def restore_config_to_default():
    def_config = """\
# RESTORED DEFAULTS:

# Path to the input folder:
corpus_path = ""

# list of folder names to be excluded from metadata generation:
exclude = (["OpenITI.github.io", "Annotation", "maintenance", "i.mech00",
            "i.mech01", "i.mech02", "i.mech03", "i.mech04", "i.mech05",
            "i.mech06", "i.mech07", "i.mech08", "i.mech09", "i.logic",
            "i.cex", "i.cex_Temp", "i.mech", "i.mech_Temp", ".git"])

# Set to True if the data is in 25-year folders, False if they are not:
data_in_25_year_repos = None  # True/False

# Set to True if the script needs to check completeness of the yml files:
perform_yml_check = None  # True/False

# Set to True if the script needs to update the token counts in the yml files:
check_token_counts = None  # True/False

# Set to True if the script needs to include character length in the yml files:
incl_char_length = None  # True/False

# Split title and author data in Arabic and Latin script into separate columns:
split_ar_lat = None  # True/False

# path to the output folder:
output_path = "./output/"

# Use this path instead of the `corpus_path` for text and yml files in output metadata:
# E.g., "https://raw.githubusercontent.com/OpenITI", ".."
output_files_path = None  # write path to use instead of corpus_path

# path to the output files (default: in the folder at output_path)
meta_tsv_fp = None
meta_yml_fp = None
meta_json_fp = None
meta_header_fp = None

# List of lists (description, run_id on server):  
passim_runs = [['October 2017 (V1)', 'passim1017'],
               ['February 2019 (V2)', 'passim01022019'],
#               ['May 2019 (Aggregated)', 'aggregated01052019'],
               ['February 2020', 'passim01022020'],
               ['October 2020', 'passim01102020']]

# Set to True to allow the script to make changes to yml files without asking:
silent = False  # True/False"""
    
    with open("utility/config.py", mode="w", encoding="utf-8") as file:
        file.write(def_config)

def check_input(msg, responses={"Y": True, "N": False}):
    print(msg)
    responses = {k.upper(): v for k,v in responses.items()}
    r = input("{}? ".format("/".join(responses.keys())))
    if r.upper() in responses:
        return responses[r.upper()]
    else:
        print("Response not recognized. Try again:")
        return check_input(msg, responses)

def get_github_issues(token_fp="GitHub personalAccessTokenReadOnly.txt"):
    try:
        with open(token_fp, mode="r", encoding="utf-8") as file:
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
    return issues_uri_dict

def supplement_config_variables(cfg_dict, v_list):
    """Check if all vars in v_list are in config_dict; \
    add missing vars with value None."""
    for v in v_list:
        if v not in cfg_dict:
            cfg_dict[v] = None

def read_config(config_pth):
    """Read the config file into a dictionary

    NB: Python's ConfigParser works with config files that contain sections.
        Since our config files do not have sections, a dummy section is added.
        See https://stackoverflow.com/a/25493615.
    """
    with open(config_pth, mode="r") as file:
        config_string = "[dummy_section]\n" + file.read()
    cp = configparser.ConfigParser(inline_comment_prefixes=["#"])
    cp.read_string(config_string)
    cfg_dict = dict(cp["dummy_section"])
    for k,v in cfg_dict.items():
        if v.strip() == "True":
            cfg_dict[k] = True
        elif v.strip() == "False":
            cfg_dict[k] = False
        elif v.strip() == "None":
            cfg_dict[k] = None
        elif v.strip().startswith(("(", "[", "{")):
            #cfg_dict[k] = json.loads(v.strip())
            cfg_dict[k] = eval(v.strip())
        elif v.strip().startswith(("r'", 'r"')):
            cfg_dict[k] = v.strip()[2:-1].replace("\\", "/")
            print(v, ">", v.strip()[2:-1].replace("\\", "/"))
        elif v.strip().startswith(("'", '"')):
            cfg_dict[k] = v.strip()[1:-1]
    return cfg_dict
    

def setup_25_years_folders_test(test_folder="test/25-years-folders",
                          temp_folder="test/temp"):
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    shutil.copytree(test_folder, temp_folder)


def setup_release_structure_test(test_folder="test/25-years-folders",
                          temp_folder="test/temp"):
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    os.mkdir(temp_folder)
    
    for folder in os.listdir(test_folder):
        folder_pth = os.path.join(test_folder, folder, "data")
        for case in os.listdir(folder_pth):
            case_pth = os.path.join(folder_pth, case)
            dst = os.path.join(temp_folder, case)
            shutil.copytree(case_pth, dst)

def setup_flat_structure_test(test_folder="test/25-years-folders",
                        temp_folder="test/temp"):
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    os.mkdir(temp_folder)    
    for folder in os.listdir(test_folder):
        folder_pth = os.path.join(test_folder, folder, "data")
        for root, dirs, files in os.walk(folder_pth):
            for fn in files:
                if fn.startswith("0"):
                    fp = os.path.join(root, fn)
                    shutil.copyfile(fp, os.path.join(temp_folder, fn))

def check_thurayya_uris(pth_string):
    with open("utility/Thurayya_URIs.csv", mode="r", encoding="utf-8") as file:
        thurayya_uris = set(file.read().splitlines())
    print("Places that are not in al-Thurayya:")
    R_O_W_uris = []
    XXXYYY_uris = []
    auto_uris = []
    error_uris = []
    any_errors = False
    for uri in geo_URIs:
        if uri not in thurayya_uris:
            if uri.endswith(("Auto", "AUTO", "auto")):
                auto_uris.append(uri)
            elif "XXXYYY" in uri:
                XXXYYY_uris.append(uri)
            else:
                error_uris.append(uri)
##                print("*", uri)
##                for author_yml in geo_URIs[uri]:
##                    print("  -", author_yml)
        elif uri.endswith(("_R","_O","_W")):
            R_O_W_uris.append(uri)
    if error_uris:
        any_errors = True
        print("-"*80)
        print("These URIs seem to be faulty:")
        for uri in sorted(error_uris):
            print("*", uri)        
    if auto_uris:
        any_errors = True
        print("-"*80)
        print("These URIs have been assigned only based on nisba and must be checked:")
        for uri in sorted(auto_uris):
            print("*", uri)
##            for author_yml in geo_URIs[uri]:
##                print("  -", author_yml)
    if XXXYYY_uris:
        any_errors = True
        print("-"*80)
        print("These URIs should be added to Thurayya:")
        for uri in sorted(XXXYYY_uris):
            print("*", uri)
##            for author_yml in geo_URIs[uri]:
##                print("  -", author_yml)
    if R_O_W_uris:
        any_errors = True
        print("-"*80)
        print("Thurayya URIs that exist but end with _R, _O or _W instead of _S:")
        for uri in sorted(R_O_W_uris):
            print("*", uri)
##            for author_yml in geo_URIs[uri]:
##                print("  -", author_yml)
    if not any_errors:
        print("    no problems found with Thurayya URIs")
    else:
        print("-"*80)
        print("YML files that contain Thurayya URI issues can be found in")
        print(pth_string+"Thurayya_URIs_to_be_checked.csv")

    # write details to file:
    csv_list = []
    error_lists = [error_uris, auto_uris, XXXYYY_uris, R_O_W_uris]
    error_labels = ["error", "auto", "XXXYYY", "R_O_W"]
    for i, lst in enumerate([error_uris, auto_uris, XXXYYY_uris, R_O_W_uris]):
        for uri in lst:
            for author_yml in geo_URIs[uri]:
                csv_list.append("{}\t{}\t{}".format(error_labels[i], uri, author_yml))
    fp = pth_string+"_Thurayya_URIs_to_be_checked.csv"
    with open(fp, mode="w", encoding="utf-8") as file:
        file.write("URI problem type\tThurayya URI\tAuthor YML\n")
        file.write("\n".join(sorted(csv_list)))        
    print("="*80)


def main():
    
    info = """\
Command line arguments for generate-metadata.py:

-h, --help : print help info
-t, --token_counts : update character and token counts
                     => sets check_token_counts variable to True
-l, --char_length : include character counts in metadata
                    => sets incl_char_length to True
-f, --flat_data : data not in 25 year repos
                  => sets data_in_25_year_repos to False
-d, --restore_default : restore values in config.py to default
-r, --recheck_yml : include a check of whether all yml files are complete
-p, --split_ar_lat : put arabic and latin info in separate columns
-s, --silent : execute changes to yml files without asking questions

-i, --input_folder : (str) path to the input folder
                           => sets corpus_path variable
-o, --output_folder : (str) path to the output folder for metadata files
                            => sets output_path variable
                            (default = "./output/")
-t, --tsv_fp : (str) file path to the tsv output file
                     (only if you do not want it in the defined output folder)
                     => sets meta_tsv_fp variable
-y, --yml_fp : (str) file path to the yml output file
                     (only if you do not want it in the defined output folder)
                     => sets meta_yml_fp variable
-j, --json_fp : (str) file path to the json output file
                      (only if you do not want it in the defined output folder)
                      => sets out_fp variable
-a, --arab_header_fp: (str) file path to the json file 
                            that will contain all Arabic metadata 
                            extracted from text file headers.
                            (only if you do not want it in the defined output folder)
                            => sets meta_header_fp variable
-x, --exclude : (list) list of folder names to exclude from metadata
-c, --config : (str) name of a python file with custom configuration variables
                     (default: ./utility/config.py)
-z, --test : (str) test the script on one of the three different
                   folder structures: choose one out of "25_years_folders",
                   "release_structure" or "flat_structure"
"""
    argv = sys.argv[1:]
    opt_str = "htlfdprsi:o:t:y:j:a:x:c:z:"
    opt_list = ["help", "token_counts", "char_length", "flat_data",
                "restore_default", "split_ar_lat", "recheck_yml", "silent",
                "input_folder=", "output_folder=", "csv_fp=", "yml_fp=",
                "json_fp=", "arab_header_fp=", "exclude=", "config=", "test="]
    try:
        opts, args = getopt.getopt(argv, opt_str, opt_list)
    except Exception as e:
        print(e)
        print("Input incorrect: \n"+info)
        sys.exit(2)

    # 0a- import variables from config file

    configured = False
    for opt, arg in opts:
        if opt in ["-c", "--config"]:
            # load variables from custom config file provided in command line:
            print ("config", arg)
            shutil.copy(arg, "utility/temp_config.py")
            cfg_dict = read_config("utility/temp_config.py")
            os.remove("utility/temp_config.py")
            configured = True
        elif opt in ["-d", "--restore_default"]:
            restore_config_to_default()
            print("default values in config.py restored")

    if not configured: # load variables from default configuration file
        cfg_dict = read_config("utility/config.py")

    v_list = ["corpus_path", "exclude", "data_in_25_year_repos",
              "perform_yml_check", "check_token_counts",
              "incl_char_length", "output_path",
              "meta_tsv_fp", "meta_yml_fp", "meta_json_fp", "meta_header_fp",
              "passim_runs", "silent", "split_ar_lat", "output_files_path",
              "remove_from_path"]
    supplement_config_variables(cfg_dict, v_list)

    corpus_path = cfg_dict["corpus_path"]
    exclude = cfg_dict["exclude"]
    data_in_25_year_repos = cfg_dict["data_in_25_year_repos"]
    perform_yml_check = cfg_dict["perform_yml_check"]
    check_token_counts = cfg_dict["check_token_counts"]
    incl_char_length = cfg_dict["incl_char_length"]
    output_path = cfg_dict["output_path"]
    meta_tsv_fp = cfg_dict["meta_tsv_fp"]
    print(meta_tsv_fp)
    meta_yml_fp = cfg_dict["meta_yml_fp"]
    meta_json_fp = cfg_dict["meta_json_fp"]
    meta_header_fp = cfg_dict["meta_header_fp"]
    passim_runs = cfg_dict["passim_runs"]
    silent = cfg_dict["silent"]
    split_ar_lat = cfg_dict["split_ar_lat"]
    output_files_path = cfg_dict["output_files_path"]
    remove_from_path = cfg_dict["remove_from_path"]
    flat_folder = False

    print("output_files_path", output_files_path)


    # 0b- override config variables from command line arguments:

    for opt, arg in opts:
        if opt in ["-h", "--help"]:
            print(info)
            return
        elif opt in ["-t", "--token_counts"]:
            check_token_counts = True
            print("check_token_counts", check_token_counts)
        elif opt in ["-l", "--char_length"]:
            incl_char_length = True
            print("incl_char_length", incl_char_length)
        elif opt in ["-f", "--flat_data"]:
            data_in_25_year_repos = False
            print("data_in_25_year_repos", data_in_25_year_repos)
        elif opt in ["-p", "--split_ar_lat"]:
            split_ar_lat = True
            print("split_ar_lat", split_ar_lat)
        elif opt in ["-r", "--recheck_yml"]:
            perform_yml_check = True
            print("perform_yml_check", perform_yml_check)
        elif opt in ["-s", "--silent"]:
            silent = True
            print("silent", silent)
        elif opt in ["-i", "--input_folder"]:
            corpus_path = arg
            print("corpus_path", corpus_path)
        elif opt in ["-o", "--output_folder"]:
            output_path = arg
            print("output_path", output_path)
        elif opt in ["-t", "--tsv_fp"]:
            meta_tsv_fp = arg
            print("meta_tsv_fp", meta_tsv_fp)
        elif opt in ["-y", "--yml_fp"]:
            meta_yml_fp = arg
            print("meta_yml_fp", meta_yml_fp)
        elif opt in ["-j", "--json_fp"]:
            meta_json_fp = arg
            print("out_fp", out_fp)
        elif opt in ["-a", "--arab_header_fp"]:
            meta_header_fp = arg
            print("meta_header_fp", meta_header_fp)
        elif opt in ["-x", "--exclude"]:
            exclude = arg
            print("exclude", exclude)
        elif opt in ["-z", "--test"]:
            if arg == "25_years_folders":
                setup_25_years_folders_test()
                data_in_25_year_repos = True
            elif arg == "release_structure":
                setup_release_structure_test()
                data_in_25_year_repos = False
                flat_folder = False
            elif arg == "flat_structure":
                setup_flat_structure_test()
                data_in_25_year_repos = False
                flat_folder = True
            else:
                print(arg, "is not a correct value for the -z/--test parameter")
                print("Choose one out of:")
                print("* 25_years_folders")
                print("* release_structure")
                print("* flat_structure")
                sys.exit(2)


    # 0c- deal with variables that remain undefined:
 
    if not corpus_path:
        msg = "Insert the path to the parent folder of the repos: "
        corpus_path = input(msg)
        print("Metadata will be collected in", corpus_path)

    if output_files_path == None:
        msg = "Do you want to use another path (e.g., relative path, URL) to this folder in the output file?"
        print(msg)
        r = input("Y/N? ")
        if r.lower() == "y":
            msg = "Write the path to the parent folder of the repos for use in output file: "
            output_files_path = input(msg)
 
    if data_in_25_year_repos == None:
        msg = "Is the data in 25-years folders? (press 'N' for RELEASE data)"
        data_in_25_year_repos = check_input(msg)
        if not data_in_25_year_repos:
            msg = "Is the folder structure entirely flat? "
            flat_folder = check_input(msg)
    URI.data_in_25_year_repos = data_in_25_year_repos

    if perform_yml_check == None:
        msg = "Do you want to check completeness of the yml files?"
        perform_yml_check = check_input(msg)
        if perform_yml_check:
            print("Do you want to re-calculate the Arabic token length of every text?")
            print("This may take up to an hour on a slow machine.")
            resp = input("Y/N: ")
            if resp == "Y":
                check_token_counts = True
            else:
                check_token_counts = False
 
    if incl_char_length == None:
        msg = "Do you want to include character count in addition to token count?"
        incl_char_length = check_input(msg)

    if split_ar_lat == None:
        msg = "Do you want to keep Arabic and Latin metadata in separate columns?"
        split_ar_lat = check_input(msg)



    pth_string = re.sub(r"\.+[\\/]", "", corpus_path)
    pth_string = re.sub(r"[:\\/]+", "_", pth_string)
    pth_string = os.path.join(output_path, pth_string)
    if meta_yml_fp == None: 
        meta_yml_fp = pth_string + "_metadata_complete.yml"
    if meta_tsv_fp == None: 
        meta_tsv_fp = pth_string + "_metadata_light.csv"
    if meta_json_fp == None:
        meta_json_fp = pth_string + "_metadata_light.json"
    if meta_header_fp == None:
        meta_header_fp = pth_string + "_header_metadata.json"
    book_rel_fp = pth_string + "_book_relations.json"
    name_el_fp = pth_string + "_name_elements.json"


    print("corpus_path", corpus_path)
    print("exclude", exclude)
    print("data_in_25_year_repos", data_in_25_year_repos)
    print("perform_yml_check", perform_yml_check)
    print("check_token_counts", check_token_counts)
    print("incl_char_length", incl_char_length)
    print("output_path", output_path)
    print("meta_tsv_fp", meta_tsv_fp)
    print("meta_yml_fp", meta_yml_fp)
    print("meta_json_fp", meta_json_fp)
    print("meta_header_fp", meta_header_fp)
    print("silent", silent)
    print("data_in_25_year_repos", data_in_25_year_repos)
    print("flat_folder", flat_folder)
    print("output_files_path", output_files_path)

    if not silent:
        input("Press Enter to start generating metadata ")

    start = time.time()
        
    # 1a- check and update yml files:

    if perform_yml_check:
        print("Checking yml files before collecting metadata...")
        # execute=False forces the script to show you all changes it wants to make
        # before prompting you whether to execute the proposed changes:
        check_yml_files(corpus_path, exclude=exclude,
                        execute=silent, check_token_counts=check_token_counts,
                        flat_folder=flat_folder)
        print()
        end = time.time()
        print("Processing time: {0:.2f} sec".format(end - start))

    # 1b- collect metadata and save to csv:

    end = time.time()
    print("="*80)
    print("Collecting metadata...")
    collectMetadata(corpus_path, exclude, meta_tsv_fp, meta_yml_fp,
                    book_rel_fp, name_el_fp, incl_char_length=incl_char_length,
                    split_ar_lat=split_ar_lat, flat_folder=flat_folder,
                    output_files_path=output_files_path,remove_from_path=remove_from_path)
    temp = end
    end = time.time()
    print("Processing time: {0:.2f} sec".format(end - start))

    # 1c - get github issues:

    print("="*80)
    #print("SKIPPING COLLECTING ISSUES FROM GITHUB")
    #issues_uri_dict = dict()
    print("Collecting issues from GitHub...")
    # UNCOMMENT!
    issues_uri_dict = get_github_issues()
    temp = end
    end = time.time()
    print("GitHub fetching time: {0:.2f} sec".format(end - temp))
    
    # 2a - Save main metadata

    print("="*80)
    print("Saving metadata...")
    print("="*80)

    createJsonFile(meta_tsv_fp, meta_json_fp, passim_runs, issues_uri_dict)

    
    # 2b- Save header metadata

    with open(meta_header_fp, mode="w", encoding="utf-8") as file:
        json.dump(all_header_meta, file, ensure_ascii=False)


    # 3a- check Thurayya URIs:
    check_thurayya_uris(pth_string)

        
    # 3b- check duplicate ids:
    duplicate_ids = False
    for version_id, uris in version_ids.items():
        if len(uris) > 1:
            duplicate_ids = True
            print("DUPLICATE ID:", uris)
    if not duplicate_ids:
        print("NO DUPLICATE IDS FOUND")
    print("="*80)
            

    print("Tada!")
    print("Total processing time: {0:.2f} sec".format(end - start))




if __name__ == "__main__":
    main()
