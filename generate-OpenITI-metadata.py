import time
import re
import os
import shutil
import textwrap
import sys
import csv
import json
from utility import betaCode
from utility import zfunc

start = time.time()
splitter = "##RECORD"+"#"*64+"\n"
output_path = "./output/"
meta = output_path + "OpenITI_metadata_light.csv"

def LoadTags():
    mapping_file = "./utility/ID_TAGS.txt"
    with open(mapping_file, "r", encoding="utf8") as f1:
        dic = {}
        data = f1.read().split("\n")

        for d in data:
            d = d.split("\t")
            dic[d[0]] = d[1]
    return dic

tagsDic = LoadTags()


# def extendTags(meta):
#     with open(meta, "r", encoding="utf8") as f1:
#         dic = {}
#         data = f1.read().split("\n")

#         for d in data[1:]:
#             d = d.split("\t")
#             print(d)
#             bookURI = d[3]
#             tags    = d[9]

#             if tags != "NONE":
#                 dic[bookURI] = tags
#     return(dic)

# extendedTags = extendTags(meta)

def CreateJsonFile(filename):
    json_objects = []
    webserver_url = 'http://dev.kitab-project.org/'

    with open(filename) as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        record = {}

        for row in reader:
            record = row
            # Create a URL for KITAB Web Server for SRT Files
            new_id = row['url'].split('/')[-1].split('.')[-1]
            record['srts'] = [
                webserver_url+ 'passim1017/' + new_id,
                webserver_url+ 'passim01022019/' + new_id,
                webserver_url+ 'aggregated01052019/' + new_id
            ]
            json_objects.append(record)

    # The required format for json file is data:[{jsonobjects}]
    first_json_key = {}
    first_json_key['data'] = json_objects
    json_file = open(output_path+'OpenITI_metadata_light.json', 'w')

    return json.dump(first_json_key, json_file)
    print("JSON file generated...")


def collectMetadata(folder):

    print()
    # print("Processing:")
    # print("\t"+folder)
    # print()
    print("\t\tcollecting metadata from OpenITI...")
    print()
    # input()

    dataYML = []
    dataCSV = {}  # vers-uri, date, author, book, id, status, length, fullTextURL, instantiationURL, tags, localPath
    statusDic = {}

    counter = 0
    priCoun = 0

    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in zfunc.exclude]
        for file in files:
            if re.search("^\d{4}[A-Za-z]+\.[A-Za-z\d]+\.\w+-(ara|per)\d\.yml$", file):
                uri = file[:-4]

                versF = os.path.join(root, file)
                bookF = re.sub("\.[a-zA-Z0-9]+-ara\d\.yml", ".yml", versF)

                authTemp = versF.split("/")
                # print(authTemp)
                authF = "/".join(authTemp[:5])+"/"+authTemp[4]+".yml"
                #print("versF ", versF)

                #print("\t"+ versF)
                vers = zfunc.dicToYML(zfunc.readYML(versF)) + "\n"
               
                #print("\t"+ bookF)
                book = zfunc.dicToYML(zfunc.readYML(bookF)) + "\n"

                #print("\t"+ authF)
                auth = zfunc.dicToYML(zfunc.readYML(authF)) + "\n"

                record = splitter + vers + book + auth
                dataYML.append(record)

                # csv
                iUrl = "https://raw.githubusercontent.com/OpenITI/instantiation/master/data/"

                versD = zfunc.readYML(versF)

                versUri = versD["00#VERS#URI######:"].strip()
                uriList = versUri.split(".")

                # print(versF)
                # print(versUri)
                date = str(int(versUri[:4]))
                author = uriList[0]
                book = uriList[0]+"."+uriList[1]
                idFile = uriList[-1].split("-")[0]
                length = versD["00#VERS#LENGTH###:"].strip()
                fullText = zfunc.pathsFromURI(versUri)[-1]+versUri
                # input(fullText)
                inst = iUrl + uriList[-1] + "/"
                status = "sec"

                # status test: first, check, if there is a preferred file already, punish Sham30K
                p = zfunc.pathsFromURI(versUri)[-2]+versUri
                # input(p)
                if os.path.isfile(p+".inProgress"):
                    lenTemp = 100000000
                    fullText += ".inProgress"
                elif os.path.isfile(p+".completed"):
                    lenTemp = 100000000
                    fullText += ".completed"
                elif os.path.isfile(p+".mARkdown"):
                    lenTemp = 100000000
                    fullText += ".mARkdown"

                elif "Sham30K" in versUri:
                    lenTemp = 0
                else:
                    lenTemp = length

                if book in statusDic:
                    statusDic[book].append("%010d##" % int(lenTemp) + versUri)
                else:
                    statusDic[book] = []
                    statusDic[book].append("%010d##" % int(lenTemp) + versUri)

                if idFile in tagsDic:
                    tags = tagsDic[idFile]
                    #print(idFile, tagsDic[idFile])
                else:
                    tags = "NONE"

                

                lp = p.replace(corpus_path, "/")
                value = "\t".join([versUri, date, author, book,
                                  idFile, status, length, fullText, inst, lp, tags])
                dataCSV[versUri] = value

                # print(dataCSV)

    for k, v in statusDic.items():
        v = sorted(v, reverse=True)

        key = v[0].split("##")[1]

        dataCSV[key] = dataCSV[key].replace("\\tsec\\t", "\\tpri\\t")

    dataCSV_New = []
    print("="*80)
    print("COLLECTING INTO A CSV FILE:")
    print("="*80)

    for k, v in dataCSV.items():
        print("\t"+k)
        dataCSV_New.append(v)

    dataCSV = sorted(dataCSV_New)

    metadataFile = output_path + "OpenITI_metadata_complete.yml"
    with open(metadataFile, "w", encoding="utf8") as f9:
        f9.write("\n".join(dataYML))

    metadataFile = output_path + "OpenITI_metadata_light.csv"
    header = "\t".join(["versionUri", "date", "author", "book", "id",
                       "status", "length", "url", "instantiation", "localPath", "tags"])
    with open(metadataFile, "w", encoding="utf8") as f9:
        f9.write(header+"\n"+"\n".join(dataCSV).replace(" ", ""))


corpus_path = "../OpenITI"

print(os.listdir(corpus_path))

# collecting and saving metadata
collectMetadata(corpus_path)
end = time.time()
print("Processing time: {0:.2f} sec".format(end - start))
print("Generating JSON file....")

## creating a json file
CreateJsonFile(meta)

print("Tada!")
