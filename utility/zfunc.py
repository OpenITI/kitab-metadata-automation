import re, os, shutil, sys, textwrap

#arRa = re.compile("\b[ذ١٢٣٤٥٦٧٨٩٠ّـضصثقفغعهخحجدًٌَُلإإشسيبلاتنمكطٍِلأأـئءؤرلاىةوزظْلآآ]+\b")
arRa = re.compile(r"\b[ذّـضصثقفغعهخحجدًٌَُلإإشسيبلاتنمكطٍِلأأـئءؤرلاىةوزظْلآآ]+\b")

exclude = (["OpenITI.github.io", "Annotation", "maintenance", "i.mech00", "i.mech01",
            "i.mech02", "i.mech03", "i.mech04", "i.mech05", "i.mech06", "i.mech07",
            "i.mech08", "i.mech09", "i.logic", "i.cex", "i.cex_Temp", "i.mech", "i.mech_Temp"])

import math 
def roundup(x, par):
    newX = int(math.ceil(int(x) / float(par)) * par)
    return(newX)

def pathsFromURI(uri):
    # /Users/romanov/Documents/a.UCA_Centennial/OpenITI/
    # /0600AH/data/0581IbnTufayl/0581IbnTufayl.HayyIbnYaqzan/0581IbnTufayl.HayyIbnYaqzan.Shamela0009734-ara1
    curPath = os.getcwd()
    curPath = curPath.replace("maintenance", "")
    #print(curPath)
    # locFul
    # locRel: repo"/data/"author/authorBook/uri
    repo = "%04dAH" % roundup(int(uri[:4]), 25)
    auth = uri.split(".")[0]
    book = uri.split(".")[1]
    path = repo+"/data/"+auth+"/"+auth+"."+book+"/"
    locRel = "../"+path
    # locFul
    locFul = curPath+path
    # remote https://raw.githubusercontent.com/OpenITI/ + replace("/data/", "/master/data/")
    rem = "https://raw.githubusercontent.com/OpenITI/"
    remote = rem + path.replace("/data/", "/master/data/")
    return(locRel, locFul, remote)           

def mainPaths(uri):
    curPath = os.getcwd()
    curPath = curPath.replace("maintenance", "")
    # locRel: repo"/data/"author/authorBook/uri
    repo = "%04dAH" % roundup(int(uri[:4]), 25)
    auth = uri.split(".")[0]
    book = uri.split(".")[1]
    pathB = repo+"/data/"+auth+"/"+auth+"."+book+"/"
    pathA = repo+"/data/"+auth+"/"
    authFul = curPath+pathA
    bookFul = curPath+pathB
    return(authFul, bookFul)

def readYML(file):
    dic = {}
    with open(file, "r", encoding="utf8") as f1:
        data = f1.read()
        
        data = re.sub("\n+$", "", data)
        data = re.sub("-\n[ \t]+", "-", data)
        data = re.sub("\n[ \t]+", " ", data)
        data = data.split("\n")
        for d in data:
            d = re.split(r"(^[\w#]+:)", d)
            dic[d[1]] = d[2].strip()
            #print(d[1])
    return(dic)

def betaCodeDic(dic):
    dicNew = {}
    for k,v in dic.items():
        if re.search("^[abc]?11#.*#AR:$", k):
            dicNew[k] = betaCode.betacodeToTranslit(v)
            kAr = k.replace("10#", "11#")
            dicNew[kAr] = betaCode.betaCodeToArSimple(betaCode.betacodeToTranslit(v))
        else:
            dicNew[k] = v
            
    return(dicNew)
        

def dicToYML(dic):
    data = []
    for k,v in dic.items():
        i = k+" "+str(v)
        if "#URI#" in i:
            pass
        else:
            i = "\n    ".join(textwrap.wrap(i, 72))
        data.append(i)

    data = "\n".join(sorted(data))
    #print(data)
    return(data)   

def dicUpdate(mainDic, updateDic):
    if updateDic != {}:
        for k,v in updateDic.items():
            if k not in mainDic:
                mainDic[k] = v
    return(mainDic)

def wordsInText(pathToFile):
    with open(pathToFile, "r", encoding="utf8") as f1:
        text = f1.read()

        test = "#META#Header#End#"

        if test in text:
            text = text.split(test)[1]
            words = len(arRa.findall(text))
        else:
            input("Warning! The file does not conform to OpenITI mARkdown scheme!!!")
            words = 0

    return(words)

def countWords(pathFull):
    if os.path.isfile(pathFull+".mARkdown"):
        num = wordsInText(pathFull+".mARkdown")
    elif os.path.isfile(pathFull+".completed"):
        num = wordsInText(pathFull+".completed")
    elif os.path.isfile(pathFull+".inProgress"):
        num = wordsInText(pathFull+".inProgress")
    else:
        num = wordsInText(pathFull)
    return(num)