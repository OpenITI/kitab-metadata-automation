import re

###################################################################################
# BetaCode Tables: Beginning ######################################################
###################################################################################

# The file includes three conversion tables.
# - betacodeTranslit: one-to-one unconventional
# - translitLOC:      Library of Congress Romanization of Arabic
# - translitSearch:   simplified transliteration for search and alphabetization purposes

# To add
# - possibly other transliteration flavors: Brill, French, German and Spanish tranliteration system differ from LOC

# One-to-one transliteration for computational research
# - main principle: one Arabic character = one Latin character
# - understandable for Arabists, but has some unconventional symbols

betacodeTranslit = {
# Alphabet letters
    '_a' : 'ā', # alif
    'b'  : 'b', # bā’
    'p'  : 'p', # pe / Persian
    't'  : 't', # tā’
    '_t' : 'ṯ', # thā’
    '^g' : 'ǧ', # jīm
    'j'  : 'ǧ', # jīm
    '^c' : 'č', # chīm / Persian
    '*h' : 'ḥ', # ḥā’
    #'.h' : 'ḥ', # ḥā’
    '_h' : 'ḫ', # khā’
    'd'  : 'd', # dāl
    '_d' : 'ḏ', # dhāl
    'r'  : 'r', # rā’
    'z'  : 'z', # zayn
    's'  : 's', # sīn
    '^s' : 'š', # shīn
    '*s' : 'ṣ', # ṣād
    #'.s' : 'ṣ', # ṣād
    '*d' : 'ḍ', # ḍād
    #'.d' : 'ḍ', # ḍād
    '*t' : 'ṭ', # ṭā’
    #'.t' : 'ṭ', # ṭā’
    '*z' : 'ẓ', # ẓā’
    #'.z' : 'ẓ', # ẓā’
    '`'  : 'ʿ', # ‘ayn
    '*g' : 'ġ', # ghayn
    #'.g' : 'ġ', # ghayn
    'f'  : 'f', # fā’
    '*k' : 'ḳ', # qāf
    #'.k' : 'ḳ', # qāf
    #'q'  : 'ḳ', # qāf
    'k'  : 'k', # kāf
    'g'  : 'g', # gāf / Persian
    'l'  : 'l', # lām
    'm'  : 'm', # mīm
    'n'  : 'n', # nūn
    'h'  : 'h', # hā’
    'w'  : 'w', # wāw
    '_u' : 'ū', # wāw
    'y'  : 'y', # yā’
    '_i' : 'ī', # yā’
# Non-alphabetic letters
    '\'' : 'ʾ', # hamzaŧ
    '/a' : 'á', # alif maqṣūraŧ
    #':t' : 'ŧ', # tā’ marbūṭaŧ, add +, it in idafa (`_amma:t+ ba*gd_ad)
    '=t' : 'ŧ', # tā’ marbūṭaŧ, this is preferable for Alpheios
# Vowels
    '~a' : 'ã', # dagger alif
    'u'  : 'u', # ḍammaŧ    
    'i'  : 'i', # kasraŧ
    'a'  : 'a', # fatḥaŧ
    '?u'  : 'ủ', # ḍammaŧ    
    '?i'  : 'ỉ', # kasraŧ
    '?a'  : 'ả', # fatḥaŧ    
    #'.n' : 'ȵ',  # n of tanwīn
    #'^n' : 'ȵ',  # n of tanwīn
    #'_n' : 'ȵ',  # n of tanwīn
    '*n' : 'ȵ',   # n of tanwīn
    '*w' : 'ů',  # silent w, like in `Amru.n.w
    '*a' : 'å'  # silent alif, like in fa`al_u.a    
    }

# conventional US/LOC transliteration
translitLOC = {
# Alphabet letters
    'ā' : 'ā',  # alif
    'b' : 'b',  # bā’
    'p' : 'p', # pe / Persian
    't' : 't',  # tā’
    'ṯ' : 'th', # thā’
    'ǧ' : 'j',  # jīm
    'č' : 'ch', # chīm / Persian
    'ḥ' : 'ḥ',  # ḥā’
    'ḫ' : 'kh', # khā’
    'd' : 'd',  # dāl
    'ḏ' : 'dh', # dhāl
    'r' : 'r',  # rā’
    'z' : 'z',  # zayn
    's' : 's',  # sīn
    'š' : 'sh', # shīn
    'ṣ' : 'ṣ',  # ṣād
    'ḍ' : 'ḍ',  # ḍād
    'ṭ' : 'ṭ',  # ṭā’
    'ẓ' : 'ẓ',  # ẓā’
    'ʿ' : 'ʿ',   # ‘ayn
    'ġ' : 'gh', # ghayn
    'f' : 'f',  # fā’
    'ḳ' : 'q',  # qāf
    'k' : 'k',  # kāf
    'g' : 'g',  # gāf / Persian
    'l' : 'l',  # lām
    'm' : 'm',  # mīm
    'n' : 'n',  # nūn
    'h' : 'h',  # hā’
    'w' : 'w',  # wāw
    'ū' : 'ū',  # wāw
    'y' : 'y',  # yā’
    'ī' : 'ī',  # yā’
# Non-alphabetic letters
    'ʾ' : 'ʾ',   # hamzaŧ
    'á' : 'ā',  # alif maqṣūraŧ
    'ŧ' : 'h',  # tā’ marbūṭaŧ
# Vowels
    'ã' : 'ā',  # dagger alif
    'a' : 'a',  # fatḥaŧ
    'u' : 'u',  # ḍammaŧ
    'i' : 'i',  # kasraŧ
    'aȵ' : 'an',  # tanwīn fatḥ
    'uȵ' : '',  # tanwīn ḍamm
    'iȵ' : '',  # tanwīn kasr
    'ů' : '',  # silent w, like in `Amru.n.w
    'å' : '',  # silent alif, like in fa`al_u.a
    'ả' : '',  # final fatḥaŧ
    'ỉ' : '',  # final ḍammaŧ
    'ủ' : '',  # final kasraŧ    
    }

# necessary for rendering searcheable lines
translitSearch = {
# Alphabet letters
    'ā' : 'a',  # alif
    'b' : 'b',  # bā’
    'p' : 'p', # pe / Persian
    't' : 't',  # tā’
    'ṯ' : 'th', # thā’
    'ǧ' : 'j',  # jīm
    'č' : 'ch', # chīm / Persian
    'ḥ' : 'h',  # ḥā’
    'ḫ' : 'kh', # khā’
    'd' : 'd',  # dāl
    'ḏ' : 'dh', # dhāl
    'r' : 'r',  # rā’
    'z' : 'z',  # zayn
    's' : 's',  # sīn
    'š' : 'sh', # shīn
    'ṣ' : 's',  # ṣād
    'ḍ' : 'd',  # ḍād
    'ṭ' : 't',  # ṭā’
    'ẓ' : 'z',  # ẓā’
    'ʿ' : '',   # ‘ayn
    'ġ' : 'gh', # ghayn
    'f' : 'f',  # fā’
    'ḳ' : 'q',  # qāf
    'k' : 'k',  # kāf
    'g' : 'g',  # gāf / Persian
    'l' : 'l',  # lām
    'm' : 'm',  # mīm
    'n' : 'n',  # nūn
    'h' : 'h',  # hā’
    'w' : 'w',  # wāw
    'ū' : 'u',  # wāw
    'y' : 'y',  # yā’
    'ī' : 'i',  # yā’
# Non-alphabetic letters
    'ʾ' : '',   # hamzaŧ
    'á' : 'a',  # alif maqṣūraŧ
    'ŧ' : 'h',  # tā’ marbūṭaŧ
# Vowels
    'ã' : 'a',  # dagger alif
    'a' : 'a',  # fatḥaŧ
    'u' : 'u',  # ḍammaŧ
    'i' : 'i',  # kasraŧ
    'aȵ' : 'an',  # tanwīn fatḥ
    'uȵ' : '',  # tanwīn ḍamm
    'iȵ' : '',  # tanwīn kasr
    'ů' : '',  # silent w, like in `Amru.n.w
    'å' : '',  # silent alif, like in fa`al_u.a
    'ả' : '',  # final fatḥaŧ
    'ỉ' : '',  # final ḍammaŧ
    'ủ' : '',  # final kasraŧ 
    }

translitArabic = {
# Alphabet letters
    'ā' : ' ا ',  # alif
    'b' : ' ب ',  # bāʾ
    'p' : ' پ ', # pe / Persian
    't' : ' ت ',  # tāʾ
    'ṯ' : ' ث ', # thāʾ
    'ǧ' : ' ج ',  # jīm
    'č' : ' چ ', # chīm / Persian
    'ḥ' : ' ح ',  # ḥāʾ
    'ḫ' : ' خ ', # khāʾ
    'd' : ' د ',  # dāl
    'ḏ' : ' ذ ', # dhāl
    'r' : ' ر ',  # rāʾ
    'z' : ' ز ',  # zayn
    's' : ' س ',  # sīn
    'š' : ' ش ', # shīn
    'ṣ' : ' ص ',  # ṣād
    'ḍ' : ' ض ',  # ḍād
    'ṭ' : ' ط ',  # ṭāʾ
    'ẓ' : ' ظ ',  # ẓāʾ
    'ʿ' : ' ع ',  # ʿayn
    'ġ' : ' غ ', # ghayn
    'f' : ' ف ',  # fā’
    'ḳ' : ' ق ',  # qāf
    'q' : ' ق ',  # qāf
    'k' : ' ك ',  # kāf
    'g' : ' گ ',  # gāf / Persian
    'l' : ' ل ',  # lām
    'm' : ' م ',  # mīm
    'n' : ' ن ',  # nūn
    'h' : ' ه ',  # hāʾ
    'w' : ' و ',  # wāw
    'ū' : ' و ',  # wāw
    'y' : ' ي ',  # yāʾ
    'ī' : ' ي ',  # yāʾ
# Non-alphabetic letters
    'ʾ' : ' ء ',  # hamza
    'á' : ' ٰى ',  # alif maqṣūraŧ
    'ŧ' : ' ة ',  # tāʾ marbūṭaŧ
# Vowels
    'ã'  : ' ٰ ',  # dagger alif
    'a'  : ' َ ',  # fatḥaŧ
    'u'  : ' ُ ',  # ḍammaŧ
    'i'  : ' ِ ',  # kasraŧ
    'aȵ' : ' ً ',  # tanwīn fatḥ
    'uȵ' : ' ٌ ',  # tanwīn ḍamm
    'iȵ' : ' ٍ ',  # tanwīn kasr
    'ů' : ' و ',  # silent w, like in `Amru.n.w
    'å' : ' ا ',  # silent alif, like in fa`al_u.a
    'ả' : ' َ ',  # final fatḥaŧ
    'ỉ' : ' ِ ',  # final ḍammaŧ
    'ủ' : ' ُ ',  # final kasraŧ 
    }

arabicBetaCode = {
# Alphabet letters
    " ا " :  "_a",   # alif
    " أ " :  "'a",   # alif
    " إ " :  "'i",   # alif
    " آ " :  "'_a",  # alif
    " ب " :  "b",   # bāʾ
    " پ " :  "p",   # pe / Persian
    " ت " :  "t",   # tāʾ
    " ث " :  "_t",  # thāʾ
    " ج " :  "^g",  # jīm
    " ح " :  "*h",  # ḥāʾ
    " خ " :  "_h",  # khāʾ
    " د " :  "d",   # dāl
    " ذ " :  "_d",  # dhāl
    " ر " :  "r",   # rāʾ
    " ز " :  "z",   # zayn
    " س " :  "s",   # sīn
    " ش " :  "^s",  # shīn
    " ص " :  "*s",  # ṣād
    " ض " :  "*d",  # ḍād
    " ط " :  "*t",  # ṭāʾ
    " ظ " :  "*z",  # ẓāʾ
    " ع " :  "`",   # ʿayn
    " غ " :  "*g",  # ghayn
    " ف " :  "f",   # fā’
    " ق " :  "q",   # qāf
    " ك " :  "k",   # kāf
    " ل " :  "l",   # lām
    " م " :  "m",   # mīm
    " ن " :  "n",   # nūn
    " ه " :  "h",   # hāʾ
    " و " :  "w",   # wāw
    " ي " :  "y",   # yāʾ
# Non-alphabetic letters
    " ء " :  "'",   # hamza
    " ئ " :  "'i",   # hamza
    " ؤ " :  "'u",  # hamza
    " ى " :  "/a",  # alif maqṣūraŧ
    " ة " :  "=t",  # tāʾ marbūṭaŧ
    " ـ " :  "",    # kashīdaŧ
# Vowels
    " ٰ " :  "~a",  # dagger alif
    " َ " :  "a",   # fatḥaŧ
    " ُ " :  "u",   # ḍammaŧ
    " ِ " :  "i",   # kasraŧ
    " ً " :  "a*n", # tanwīn fatḥ
    " ٌ " :  "u*n", # tanwīn ḍamm
    " ٍ " :  "i*n", # tanwīn kasr
    }


###################################################################################
# BetaCode Tables: End ############################################################
###################################################################################

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

###################################################################################
# ConversionFunctions: Beginning ##################################################
###################################################################################

# conversionFlow: betaCode > translit > Arabic
# conversionFlow: Arabic > betaCode :: fixing Arabic via betaCode > cleaned Arabic

# convert AH to CE (only years)
def AHCE(ah):
    ce = int(ah)-(int(ah)/33)+622
    return(int(ce))

def deNoise(text):
    noise = re.compile(""" ّ    | # Tashdid
                             َ    | # Fatha
                             ً    | # Tanwin Fath
                             ُ    | # Damma
                             ٌ    | # Tanwin Damm
                             ِ    | # Kasra
                             ٍ    | # Tanwin Kasr
                             ْ    | # Sukun
                             ٰ    | # Dagger Alif
                             ـ     # Tatwil/Kashida
                         """, re.VERBOSE)
    text = re.sub(noise, '', text)
    return(text)

# define replacement with dictionaries
def dictReplace(text, dic):
    for k, v in dic.items():
        k = k.strip()
        v = v.strip()
        text = text.replace(k, v)
        if len(v) > 1:
            vUpper = v[0].upper()+v[1:]
        else:
            vUpper = v.upper()
        text = text.replace(k.upper(), vUpper)
    return(text)

# conversion functions
def betacodeToTranslit(text):
    #print("betacodeToTranslit()")
    text = dictReplace(text, betacodeTranslit)
    text = re.sub("\+|_", "", text)
    
    return(text)

def betacodeToSearch(text):
    #print("betacodeToSearch()")
    text = dictReplace(text, betacodeTranslit)
    # fixing tāʾ marbūṭaŧs
    text = re.sub(r"ŧ\+", r"t", text)
    text = re.sub(r"ŧ", r"", text)
    text = dictReplace(text, translitSearch)
    text = re.sub("\w_", "", text)
    return(text)

def betacodeToLOC(text):
    #print("betacodeToLOC()")
    text = dictReplace(text, betacodeTranslit)
    # fixing tāʾ marbūṭaŧs
    text = re.sub(r"ŧ\+", r"t", text)
    text = re.sub(r"ŧ", r"", text)
    text = dictReplace(text, translitLOC)
    text = re.sub(r"\w_", r"", text)
    return(text)

def arabicToBetaCode(text):
    #print("arabicToBetaCode()")

    # convert optative phrases    
    text = re.sub(r"صلى الله عليه وسلم", r".sl`m", text)
    text = re.sub(r"radiyallahuanhu", r"r.dh", text)

    text = dictReplace(text, arabicBetaCode)
    
    # converting tashdids and removing Arabic residue
    text = re.sub(r"(\w)%s" % " ّ ".strip(), r"\1\1", text)
    text = re.sub(" ْ ".strip(), r"", text)
    text = re.sub(r"،", r",", text)

    # fixing artifacts
    text = re.sub(r"\b_a", r"a", text)
    text = re.sub(r"aa", r"a", text)
    text = re.sub(r"ii", r"i", text)
    text = re.sub(r"uu", r"u", text)
    text = re.sub(r"a_a", r"_a", text)
    text = re.sub(r"a/a", r"/a", text)
    text = re.sub(r"iy", r"_i", text)
    text = re.sub(r"uw", r"_u", text)
    text = re.sub(r"lll", r"ll", text)
    
    return(text)


def betacodeToArabic(text):
    cnsnnts = "btṯǧčḥḥḫdḏrzsšṣḍṭẓʿġfḳkglmnhwy"
    cnsnnts = "%s%s" % (cnsnnts, cnsnnts.upper())

    #print("betacodeToArabic()")
    text = dictReplace(text, betacodeTranslit)
    #print(text)
    text = re.sub('\+' , '', text)

    # fix irrelevant variables for Arabic script
    text = text.lower()
    text = re.sub("ủ", "u", text)
    text = re.sub("ỉ", "i", text)
    text = re.sub("ả", "a", text)

    # complex combinations
    text = re.sub(r"li-?a?ll[āã]hi?", " لِـلّٰـهِ ".strip(), text) # Convert God's Name
    text = re.sub(r"bi-?a?ll[āã]hi?", "بِاللهِ", text) # Convert God's Name
    text = re.sub(r"wa-?a?ll[āã]hi?", "وَاللهِ", text) # Convert God's Name
    text = re.sub("all[ãā]h", " ﭐلـلّٰـه ".strip(), text) # Convert God's Name
    text = re.sub(r"\bb\.", "بن", text) # Convert b. into ar bn

    sun = "tṯdḏrzsšṣḍṭẓln"
    text = re.sub(r"\bal-([%s])" % sun, r"ﭐل-\1\1", text) # converts articles w/ sun letters
    text = re.sub(r"\bal-", r"ﭐلْ-", text) # converts articles
    text = re.sub(r"\bwa-a?l-", "وَﭐل-", text) # converts articles
    #text   = re.sub(r"n-", "", text) # converts articles

    text  = re.sub(",", "،", text) # Convert commas

    # initial HAMZAs
    text = re.sub("\\bʾ?a", "أَ", text)
    text = re.sub("\\bʾi", "إِ", text)
    text = re.sub("\\bi", "ﭐ", text)
    text = re.sub("\\bʾ?u", "أُ", text)
    text = re.sub("\\bʾ?ā", "آ", text)
    text = re.sub("\\bʾ?ī", "إِي", text)
    text = re.sub("\\bʾ?ū", "أُو", text)

    # final HAMZAs
    
    text = re.sub(r'aʾ\b', "أ", text)
    text = re.sub(r'uʾ\b', "ؤ", text)
    text = re.sub(r'iʾ\b', "ئ", text)
    text = re.sub(r'yʾaȵ', r"يْئًا", text)
    text = re.sub(r'([%s])ʾuȵ' % cnsnnts, r"\1%s" % "ْءٌ", text)
    text = re.sub(r'([%s])ʾiȵ' % cnsnnts, r"\1%s" % "ْءٍ", text)
    text = re.sub(r'([%s])ʾaȵ' % cnsnnts, r"\1%s" % "ْءًا", text)

    # short, hamza, tanwin
    text = re.sub(r'uʾuȵ', r"ُؤٌ", text)
    text = re.sub(r'uʾiȵ', r"ُؤٍ", text)
    text = re.sub(r'uʾaȵ', r"ُؤًا", text)

    text = re.sub(r'iʾuȵ', r"ِئٌ", text)
    text = re.sub(r'iʾiȵ', r"ِئٍ", text)
    text = re.sub(r'iʾaȵ', r"ِئًا", text)

    text = re.sub(r'aʾuȵ', r"َأٌ", text)
    text = re.sub(r'aʾiȵ', r"َأٍ", text)
    text = re.sub(r'aʾaȵ', r"َأً", text)

    # long, hamza, tanwin
    text = re.sub(r'ūʾuȵ', r"وءٌ", text)
    text = re.sub(r'ūʾiȵ', r"وءٍ", text)
    text = re.sub(r'ūʾaȵ', r"وءً", text)

    text = re.sub(r'īʾuȵ', r"يءٌ", text)
    text = re.sub(r'īʾiȵ', r"يءٍ", text)
    text = re.sub(r'īʾaȵ', r"يءً", text)

    text = re.sub(r'āʾuȵ', r"اءٌ", text)
    text = re.sub(r'āʾiȵ', r"اءٍ", text)
    text = re.sub(r'āʾaȵ', r"اءً", text)

    # long, hamza, diptote
    text = re.sub(r'āʾu\b', r"اءُ", text)
    text = re.sub(r'āʾi\b', r"اءِ", text)
    text = re.sub(r'āʾa\b', r"اءَ", text)
    
    # medial HAMZAs
    text = re.sub(r"aʾū", r"َؤُو", text)
    text = re.sub(r"uʾa", r"ُؤَ", text)
    text = re.sub(r"uʾi", r"ُئِ", text)

    text = re.sub(r"ūʾu", r"ُوؤُ", text)
    text = re.sub(r"ūʾi", r"ُوئِ", text)
    text = re.sub(r"awʾa", r"َوْءَ", text)
    text = re.sub(r"awʾu", r"َوْءُ", text)
    
    text = re.sub(r"āʾi", r"ائِ", text)
    text = re.sub(r"aʾī", r"َئِي", text)
    text = re.sub(r"āʾī", r"ائِي", text)
    text = re.sub(r"āʾu", r"اؤُ", text)
    text = re.sub(r"uʾā", r"ُؤَا", text)

    text = re.sub(r"aʾa", r"َأَ", text)
    text = re.sub(r"aʾi", r"َئِ", text)
    text = re.sub(r"aʾu", r"َؤُ", text)

    text = re.sub(r"iʾu", r"ِئُ", text)
    text = re.sub(r"iʾi", r"ِئِ", text)
    text = re.sub(r"iʾa", r"ِئَ", text)
    text = re.sub(r"īʾa", r"ِيئَ", text)
    text = re.sub(r"īʾu", r"ِيؤُ", text)
    text = re.sub(r"iʾā", r"ِئَا", text)

    text = re.sub(r"([%s])ʾa" % cnsnnts, r"\1%s" % "ْأَ", text)
    text = re.sub(r"([%s])ʾu" % cnsnnts, r"\1%s" % "ْؤُ", text)
    text = re.sub(r"([%s])ʾū" % cnsnnts, r"\1%s" % "ْؤُو", text)
    text = re.sub(r"([%s])ʾi" % cnsnnts, r"\1%s" % "ْئِ", text)

    text = re.sub(r"uʾu", r"ُؤُ", text)
    text = re.sub(r"uʾū", r"ُؤُو", text)

    text = re.sub(r"aʾʾā", r"َأَّا", text) # geminnated hamza # dagger alif "َأّٰ", ordinary alif ""
    text = re.sub(r"aʾī", r"َئِي", text)
    text = re.sub(r"āʾī", r"ائِي", text)
    text = re.sub(r"uʾā", r"ُؤَا", text)

    text = re.sub(r"uʾ([%s])" % cnsnnts, r"%s\1" % "ُؤْ", text)
    text = re.sub(r"iʾ([%s])" % cnsnnts, r"%s\1" % "ِئْ", text)
    text = re.sub(r"aʾ([%s])" % cnsnnts, r"%s\1" % "َأْ", text)

    text = re.sub(r"aʾā", r"َآ", text) # madda: hamza, long a
    text = re.sub(r"([%s])ʾā" % cnsnnts, r"\1%s" % "ْآ", text) # madda: sukun, hamza, long a

    # pronominal suffixes
    #text = re.sub(r"-(h[ui]|hā|k[ai]|h[ui]mā?|kumā|h[ui]nna|)\b", r"\1", text)

    # consonant combinations
    text = re.sub(r"([%s])\1" % cnsnnts, r"\1" + " ّ ".strip(), text)
    # two consonants into C-sukun-C
    text = re.sub(r"([%s])([%s])" % (cnsnnts,cnsnnts), r"\1%s\2" % " ْ ".strip(), text)
    text = re.sub(r"([%s])([%s])" % (cnsnnts,cnsnnts), r"\1%s\2" % " ْ ".strip(), text)
    # final consonant into C-sukun
    text = re.sub(r"([%s])(\s|$)" % (cnsnnts), r"\1%s\2" % " ْ ".strip(), text)
    # consonant + long vowel into C-shortV-longV
    text = re.sub(r"([%s])(ā)" % (cnsnnts), r"\1%s\2" % " َ ".strip(), text)
    text = re.sub(r"([%s])(ī)" % (cnsnnts), r"\1%s\2" % " ِ ".strip(), text)
    text = re.sub(r"([%s])(ū)" % (cnsnnts), r"\1%s\2" % " ُ ".strip(), text)

    # tanwins
    text = re.sub(r'([%s])aȵ' % "btṯǧḥḥḫdḏrzsšṣḍṭẓʿġfḳklmnhwy", r"\1%s" % 'اً', text)
    text = re.sub('aȵ' , ' ً '.strip(), text)
    text = re.sub('uȵ' , ' ٌ '.strip(), text)
    text = re.sub('iȵ' , ' ٍ '.strip(), text)

    # silent letters
    text = re.sub('ů' , "و", text)
    text = re.sub('å' , "ا", text)


    text = dictReplace(text, translitArabic)
    text = re.sub("-|_|ـ", "", text)
    #text = re.sub("-", "ـ ـ", text)
    return(text)

def betaCodeToArSimple(text, lang_code=None):
    text = betacodeToArabic(text)
    text = text.replace("ﭐ", "ا")
    text = deNoise(text)
    text = re.sub(r"\bإبن\b", "ابن", text)
    replacements = {
        "ar": {},
        "fa": {
            "ك": "ک",
            "ي": "ي",
            },
        "ur": {
            "ك": "ک",
            "ي": "ي",
            }
    }
    if lang_code:
        lang_code = lang_code.lower()[:2]
        if lang_code in replacements:
            for char, repl in replacements[lang_code]:
                text = re.sub(char, repl, text)
    return(text)
    

###########################################################
# BELOW : TESTING ZONE ####################################
###########################################################
##
##testString = """
##.kul huwa all~ahu_ a.hadu.n all~ahu_ al-.samadu_ lam yalid wa-lam y_ulad wa-lam yakun lahu kufu'a.n a.hadu.n
##
##wa-.k_amat `_amma:t+u_ Ba.gd_ada_ li-yusallima al-_hal_ifa:ta_ al-Man.s_ura_ `al/a ruj_u`i-hi min al-K_ufa:ti_
##
##al-.hamdu li-Ll~ahi rabbi al-`_alam_ina_
##"""
##
##
####print("betacode")
####print(testString)
##print(betacodeToTranslit(testString))
##print(betacodeToSearch(testString))
##print(betacodeToLOC(testString))
##print(betacodeToArabic(testString))
##
##testBetaCode = """
##'amru.n 'unsu.n 'insu.n '_im_anu.n
##'_aya:tu.n '_amana mas'ala:tu.n sa'ala ra'su.n qur'_anu.n ta'_amara
##_di'bu.n as'ila:tu.n q_ari'i-hi su'lu.n mas'_ulu.n
##tak_afu'u-hu su'ila q_ari'i-hi _di'_abu.n ra'_isu.n
##bu'isa ru'_ufu.n ra'_ufu.n su'_alu.n mu'arri_hu.n
##abn_a'a-hu abn_a'u-hu abn_a'i-hi ^say'a.n _ha.t_i'a:tu.n
##.daw'u-hu .d_u'u-hu .daw'a-hu .daw'i-hi mur_u'a:tu.n
##'abn_a'i-hi bar_i'u-hu s_u'ila f_ilu.n f_annu.n f_unnu.n
##s_a'ala fu'_adu.n ^surak_a'u-hu ri'_asa:tu.n tahni'a:tu.n
##daf_a'a:tu.n .taff_a'a:tu.n ta'r_i_hu.n fa'ru.n
##^say'u.n ^say'i.n ^say'a.n  
##.daw'u.n .daw'i.n .daw'a.n
##juz'u.n  juz'i.n  juz'a.n
##mabda'u.n mabda'i.n mabda'a.n
##naba'a q_ari'u.n tak_afu'u.n tak_afu'i.n tak_afu'a.n
##abn_a'u abn_a'i abn_a'a jar_i'u.n maqr_u'u.n .daw'u.n ^say'u.n juz'u.n
##`ulam_a'u al-`ulam_a'i al-`ulam_a'a
##`Amru.n.w wa-fa`al_u.a
##"""
##
###print(arabicToBetaCode(testStringArabic))
##print(betacodeToArabic(testBetaCode))
##print(betacodeToTranslit(testBetaCode))
