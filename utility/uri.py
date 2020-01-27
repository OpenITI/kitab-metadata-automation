"""A class that represents the OpenITI URI as an object.

To do:
* write function that changes all filenames and folders when a URI changes.

Examples:
    >>> from uri import URI
    >>> t = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed")

    Representations of a URI object: print() and repr():
    
    >>> print(repr(t))
    uri(date:0255, author:Jahiz, title:Hayawan, version:Sham19Y0023775, language:ara, edition_no:1, extension:completed)
    >>> print(t)
    0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed

    Accessing components of the URI:
    
    >>> t.author
    'Jahiz'
    >>> t.date
    '0255'

    Building different versions of the URI:
    
    >>> t.build_uri("author")
    '0255Jahiz'
    >>> t.build_uri("book")
    '0255Jahiz.Hayawan'
    >>> t.build_uri("version")
    '0255Jahiz.Hayawan.Sham19Y0023775-ara1'
    >>> t.build_uri("version_file")
    '0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed'
    
    Building paths based on the URI:
    
    >>> t.build_pth(uri_type="version", base_pth="D:\\test")
    'D:/test/0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.Sham19Y0023775-ara1'
    >>> t.build_pth(uri_type="version_file", base_pth="D:\\test")
    'D:/test/0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed'
    >>> t.build_pth("version")
    './0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.Sham19Y0023775-ara1'
    >>> t.build_pth()
    './0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed'
    >>> t.language=""
    >>> t.build_pth()
    './0275AH/data/0255Jahiz/0255Jahiz.Hayawan'
    >>> t.build_pth(uri_type = "book_yml")
    './0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.yml'
    
"""

import re
import os
import shutil


os.sep = "/"
ISO_CODES = re.split("[\n\r\s]+",
                     """aar abk ace ach ada ady afa afh afr ain aka akk alb sqi ale alg
alt amh ang anp apa ara arc arg arm hye arn arp art arw asm ast ath aus ava ave awa aym
aze bad bai bak bal bam ban baq eus bas bat bej bel bem ben ber bho bih bik bin bis bla
bnt tib bod bos bra bre btk bua bug bul bur mya byn cad cai car cat cau ceb cel cze ces
cha chb che chg chi zho chk chm chn cho chp chr chu chv chy cmc cnr cop cor cos cpe cpf
cpp cre crh crp csb cus wel cym cze ces dak dan dar day del den ger deu dgr din div doi
dra dsb dua dum dut nld dyu dzo efi egy eka gre ell elx eng enm epo est baq eus ewe ewo
fan fao per fas fat fij fil fin fiu fon fre fra fre fra frm fro frr frs fry ful fur gaa
gay gba gem geo kat ger deu gez gil gla gle glg glv gmh goh gon gor got grb grc gre ell
grn gsw guj gwi hai hat hau haw heb her hil him hin hit hmn hmo hrv hsb hun hup arm hye
iba ibo ice isl ido iii ijo iku ile ilo ina inc ind ine inh ipk ira iro ice isl ita jav
jbo jpn jpr jrb kaa kab kac kal kam kan kar kas geo kat kau kaw kaz kbd kha khi khm kho
kik kin kir kmb kok kom kon kor kos kpe krc krl kro kru kua kum kur kut lad lah lam lao
lat lav lez lim lin lit lol loz ltz lua lub lug lui lun luo lus mac mkd mad mag mah mai
mak mal man mao mri map mar mas may msa mdf mdr men mga mic min mis mac mkd mkh mlg mlt
mnc mni mno moh mon mos mao mri may msa mul mun mus mwl mwr bur mya myn myv nah nai nap
nau nav nbl nde ndo nds nep new nia nic niu dut nld nno nob nog non nor nqo nso nub nwc
nya nym nyn nyo nzi oci oji ori orm osa oss ota oto paa pag pal pam pan pap pau peo per
fas phi phn pli pol pon por pra pro pus qaa qtz que raj rap rar roa roh rom rum ron rum
ron run rup rus sad sag sah sai sal sam san sas sat scn sco sel sem sga sgn shn sid sin
sio sit sla slo slk slo slk slv sma sme smi smj smn smo sms sna snd snk sog som son sot
spa alb sqi srd srn srp srr ssa ssw suk sun sus sux swa swe syc syr tah tai tam tat tel
tem ter tet tgk tgl tha tib bod tig tir tiv tkl tlh tli tmh tog ton tpi tsi tsn tso tuk
tum tup tur tut tvl twi tyv udm uga uig ukr umb und urd uzb vai ven vie vol vot wak wal
war was wel cym wen wln wol xal xho yao yap yid yor ypk zap zbl zen zgh zha chi zho znd
zul zun zxx zza""")
extensions = ["inProgress", "completed", "mARkdown"]

class URI:
    """
    A class that represents the OpenITI URI as an object.
    OpenITI URIs consist of the following elements:
    0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1.mARkdown
        * VersionURI: consists of
          - EditionURI: consists of
            * Work URI: consists of
              - AuthorID: consists of
                * author's death date (self.date): 0768
                * shuhra of the author (self.author): IbnMuhammadTaqiDinBaclabakki 
              - BookID (self.title): Hadith: short title of the book
            * VersionID (self.version): Shamela0009426: ID of the collection/contributor
                from which we got the book + number of the book in that collection
          - Lang:
            * self.language: ara: ISO 639-2 language code
            * self.edition_no: 1: edition version number
        * self.extension = mARkdown (can be inProgress, mARkdown, completed, "")
    """
    def __init__(self, uri_string=None):
        """Initialize the URI object and its components: if an uri_string is provided,
        it will be split into its components.

        Args:
            uri_string (str, default: None): (a path to) an OpenITI URI, e.g.,
                0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1
                0768IbnMuhammadTaqiDinBaclabakki.Hadith
                0768IbnMuhammadTaqiDinBaclabakki
                D:\OpenITI\25Yrepos\data\0275AH\0255Jahiz
                
        Examples:
            >>> uri1 = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed")
            >>> uri2 = URI("0255Jahiz.Hayawan")
            >>> uri3 = URI()
            >>> uri4 = URI(r"D:\\OpenITI\\25Yrepos\\data\\0275AH\\0255Jahiz\\0255Jahiz.Hayawan\\0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed")
            >>> print(uri4)
            0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed
            >>> print(uri4.base_pth)
            D:\\OpenITI\\25Yrepos\\data
        """
        self.date = ""
        self.author = ""
        self.title = ""
        self.version = ""
        self.language = ""
        self.edition_no = ""
        self.extension = ""
        if uri_string:
            if len(re.split(r"[\\/]", uri_string)) > 1: # deal with paths:
                self.base_pth, self.uri_string = os.path.split(uri_string)
                # set self.base_pth to the parent of the 25Y folder:
                while not re.search("\d{4}AH", os.path.split(self.base_pth)[1]):
                    self.base_pth = os.path.split(self.base_pth)[0]
                self.base_pth = os.path.split(self.base_pth)[0]
            else:
                self.uri_string = uri_string
            self.split_uri(self.uri_string)
        else:
            self.uri_string = ""
        # make it possible to set the base_pth for every instance of the class:
        try:
            self.base_pth
        except: # if the base_pth has not been set before instantiating the class:
            self.base_pth = "."
        
##    ############################################################################
##    # Setter and getter methods: intercept mistakes when setting uri properties: 
##
##    @property
##    def date(self):
##        return self.date
##
##    @date.setter
##    def date(self, date):
##        """Set the URI's date property, after checking its conformity."""
##        self.date = self.check_date(date)
##
##
##    @property
##    def author(self):
##        return self.author
##    
##    @author.setter
##    def author(self, author):
##        """Set the URI's author property, after checking its conformity."""
##        self.author = self.check_ASCII_letters(author)
##
##
##    @property
##    def title(self):
##        return self.title
##
##    @title.setter
##    def title(self, title):
##        """Set the URI's title property, after checking its conformity."""
##        self.title = self.check_ASCII_letters(title)
##
##
##    @property
##    def version(self):
##        return self.version
##
##    @version.setter
##    def version(self, version):
##        """Set the URI's version property, after checking its conformity."""
##        self.version = self.check_ASCII(version)
##
##
##    @property
##    def language(self):
##        return self.language
##
##    @language.setter
##    def language(self, language):
##        """Set the URI's language property, after checking its conformity."""
##        self.language = self.check_language_code(language)
##


    def __call__(self, uri_type=None, ext=None):
        """Call the self.build_uri() method of the URI instance.

        Examples:
            >>> my_uri = URI("0768IbnMuhammadTaqiDinBaclabakki")
            >>> my_uri.title = "Hadith"
            >>> my_uri.version = "Shamela0009426"
            >>> my_uri.language = "ara"
            >>> my_uri.edition_no = "1"
            >>> my_uri()
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1'
            >>> my_uri("date")
            '0768'
            >>> my_uri("author")
            '0768IbnMuhammadTaqiDinBaclabakki'
            >>> my_uri("author_yml")
            '0768IbnMuhammadTaqiDinBaclabakki.yml'
            >>> my_uri("book")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith'
            >>> my_uri("book_yml")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.yml'
            >>> my_uri("version")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1'
            >>> my_uri("version_yml")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1.yml'
            >>> my_uri("version_file", ext="completed")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1.completed'
        """
        return self.build_uri(uri_type, ext)


    def __repr__(self):
        """Return a representation of the components of the URI.

        Examples:
            >>> my_uri = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1")
            >>> repr(my_uri)
            'uri(date:0255, author:Jahiz, title:Hayawan, version:Sham19Y0023775, \
language:ara, edition_no:1, extension:)'
            >>> my_uri = URI()
            >>> repr(my_uri)
            'uri(date:, author:, title:, version:, language:, edition_no:, extension:)'
        """
        component_names = "date author title version language edition_no extension"
        fmt = [x+":{"+x+"}" for x in component_names.split()]
        fmt = "uri({})".format(", ".join(fmt))
        return fmt.format(**self.__dict__)

    def __str__(self, *args, **kwargs):
        """Return the reassembled URI.

        Examples:
            >>> my_uri = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.inProgress")
            >>> my_uri.extension = "completed"
            >>> print(my_uri)
            0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed
        """
        return self.build_uri()


    def __iter__(self):
        """Enable iteration over a URI object.

        Examples:
            >>> my_uri = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.inProgress")
            >>> for component in my_uri: print(component)
            0255
            Jahiz
            Hayawan
            Sham19Y0023775
            ara
            1
            inProgress
            >>> my_uri = URI()
            >>> for component in my_uri: print(component)
            
        """
        return iter(self.split_uri())


    def get_uri_type(self):
        """Get the type of the URI object.

        Examples:
            >>> my_uri = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.inProgress")
            >>> my_uri.get_uri_type()
            'version'
            >>> my_uri = URI()
            >>> my_uri.get_uri_type() is None
            True
        """
        uri_type = None
        if self.date and self.author:
            uri_type = "author"
            if self.title:
                uri_type = "book"
                if self.version and self.language and self.edition_no:
                    uri_type = "version"
        return uri_type

    def check_ASCII_letters(self, test_string, string_type):
        """Check whether the test_string only contains ASCII letters."""
        if re.findall("[^A-Za-z]", test_string):
            msg = "{0} Error: {0} ({1}) ".format(string_type, test_string)
            msg += "should not contain digits or non-ASCII characters"
            msg += "(culprits: {})".format(re.findall("[^A-Za-z]", test_string))
            raise Exception(msg)
        return test_string

    def check_ASCII(self, test_string, string_type):
        """Check whether the test_string only contains ASCII letters and digits."""
        if re.findall("[^A-Za-z0-9]", test_string):
            msg = "{0} Error: {0} ({1}) ".format(string_type, test_string)
            msg += "should not contain non-ASCII characters"
            msg += "(culprits: {})".format(re.findall("[^A-Za-z0-9]", test_string))
            raise Exception(msg)
        return test_string

    def check_date(self, date):
        date = str(date)
        if len(date) != 4:
            msg = "Date Error: URI must start with a date of 4 digits "
            msg += "({} has {}!)".format(date, len(date))
            raise Exception(msg)
        return date

    def check_language_code(self, language):
        if not language in ISO_CODES:
            msg = "Language code ({}) ".format(language)
            msg += "should be an ISO 639-2 language code, consisting of 3 characters"
            raise Exception(msg)
        return language

    def split_uri(self, uri_string=None):
        """
        Split an OpenITI URI string into its components and check if components are valid.

        Args:
            uri_string (str): OpenITI URI, e.g.,
                0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1

        Returns:
            split_components (list): list of uri components

        Examples:
            >>> my_uri = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed")
            >>> my_uri.split_uri()
            ['0255', 'Jahiz', 'Hayawan', 'Sham19Y0023775', 'ara', '1', 'completed']
            >>> my_uri.extension=""
            >>> my_uri.language=""
            >>> my_uri.split_uri()
            ['0255', 'Jahiz', 'Hayawan']
        """
        if not uri_string:
            uri_string = self.build_uri()
        split_uri = uri_string.split(".")
        
        if split_uri == [""]:
            return []
        
        if len(split_uri) > 4:
            msg = "URI ({}) has too many parts separated by dots".format(uri_string)
            raise Exception(msg)

        self.dateAuth = split_uri[0]
        self.date = re.findall("^\d+", self.dateAuth)[0]
        self.check_date(self.date)
        self.author = self.dateAuth[4:]
        self.check_ASCII_letters(self.author, "Author name")
        if not self.author:
            msg = "No author name found. Do not put a dot between date and author name."
            raise Exception(msg)
        split_components = [self.date, self.author]
        
        if len(split_uri) > 1:
            self.title = split_uri[1]
            self.check_ASCII(self.title, "Title")
            split_components.append(self.title)
            
        if len(split_uri) > 2:    
            self.versionLang = split_uri[2]
            try:
                self.version, self.language = self.versionLang.split("-")
            except:
                raise Exception("URI () misses language ")
            self.check_ASCII(self.version, "Version ID")
            split_components.append(self.version)
            if self.language[-1].isnumeric():
                self.edition_no = re.findall("\d+", self.language)[0]
                self.language = re.sub("\d+", "", self.language)
                split_components.append(self.language)
                split_components.append(self.edition_no)                    
            else:
                self.edition_no = ""
                split_components.append(self.language)
            self.check_language_code(self.language)
        if len(split_uri) > 3:
            if split_uri[3] in extensions:
                self.extension = split_uri[3]
                split_components.append(self.extension)
            else:
##                print("ERROR: extension '{}' not in the list\
##of acceptable extensions. No extension recorded".format(split_uri[3]))
                self.extension = ""
        return split_components
            

    def build_uri(self, uri_type=None, ext=None):
        """
        Build an OpenITI URI string from its components.

        Args:
            uri_type (str; default: None): the uri type to be returned:
                - "date" : only the date (format: 0000)
                - "author" : authorUri (format: 0255Jahiz)
                - "author_yml" : filename of the author yml file
                    (format: 0255Jahiz.yml)
                - "book": BookUri (format: 0255Jahiz.Hayawan)
                - "book_yml": filename of the book yml file
                    (format: 0255Jahiz.Hayawan.yml)
                - "version": versionURI
                    (format: 0255Jahiz.Hayawan.Shamela000245-ara1)
                - "version_yml": filename of the version yml file
                    (format: 0255Jahiz.Hayawan.Shamela000245-ara1.yml)
                - "version_file": filename of the version text file
                    (format: 0255Jahiz.Hayawan.Shamela000245-ara1.completed)                

        Returns:
            uri_string (str): OpenITI URI, e.g.,
                0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1

        Examples:
            >>> my_uri = URI("0768IbnMuhammadTaqiDinBaclabakki")
            >>> my_uri.title = "Hadith"
            >>> my_uri.version = "Shamela0009426"
            >>> my_uri.language = "ara"
            >>> my_uri.edition_no = "1"
            >>> my_uri.build_uri()
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1'
            >>> my_uri.build_uri("date")
            '0768'
            >>> my_uri.build_uri("author")
            '0768IbnMuhammadTaqiDinBaclabakki'
            >>> my_uri.build_uri("author_yml")
            '0768IbnMuhammadTaqiDinBaclabakki.yml'
            >>> my_uri.build_uri("book")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith'
            >>> my_uri.build_uri("book_yml")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.yml'
            >>> my_uri.build_uri("version")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1'
            >>> my_uri.build_uri("version_yml")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1.yml'
            >>> my_uri.build_uri("version_file", ext="completed")
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1.completed'
        """
        self.uri_string = ""


        if not uri_type:
            if self.version and self.language:
                if self.extension:
                    return self.build_uri("version_file")
                else:
                    return self.build_uri("version")
            elif self.title:
                return self.build_uri("book")
            elif self.author:
                return self.build_uri("author")
            elif self.date:
                return self.build_uri("date")
            else:
                return ""
                        

        if uri_type == "date":
            if self.date:
                self.uri_string = str(self.date)
            else:
                raise Exception("Error: the date component of the URI was not defined")
        elif "author" in uri_type:
            if self.author:
                self.uri_string = "{}{}".format(self.build_uri("date"),self.author)
            else:
                raise Exception("Error: the author component of the URI was not defined")
        elif "book" in uri_type:
            if self.title:
                self.uri_string = "{}.{}".format(self.build_uri("author"), self.title)
            else:
                raise Exception("Error: the title component of the URI was not defined")
        elif "version" in uri_type:
            if self.version and self.language: 
                self.uri_string =  "{}.{}-{}{}".format(self.build_uri("book"),
                                                       self.version,
                                                       self.language,
                                                       self.edition_no)
                if "file" in uri_type:
                    if ext:
                        self.uri_string += ".{}".format(ext)
                    else:
                        if self.extension:
                            self.uri_string += ".{}".format(self.extension)
            elif self.version:
                raise Exception("Error: the language component of the URI was not defined")
            elif self.language:
                raise Exception("Error: the version component of the URI was not defined")
            else:
                raise Exception("Error: the language and version components of the URI were not defined")
        if "yml" in uri_type:
            self.uri_string += ".yml"
        return self.uri_string

    def get_version_uri(self):
        """
        Returns the version uri. 

        returns:
            uri_string (str): OpenITI URI, e.g.,
                0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1

        Example:
            >>> my_uri = URI('0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1')
            >>> my_uri.extension = "completed"
            >>> my_uri.get_version_uri()
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1'
        """
        return self.build_uri("version")
    
    def get_book_uri(self):
        """
        Returns the book uri. 

        returns:
            uri_string (str): OpenITI URI, e.g.,
                0768IbnMuhammadTaqiDinBaclabakki.Hadith

        Example:
            >>> my_uri = URI('0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1')
            >>> my_uri.get_book_uri()
            '0768IbnMuhammadTaqiDinBaclabakki.Hadith'
        """
        return self.build_uri("book")
    
    def get_author_uri(self):
        """
        Returns the author uri. 

        returns:
            uri_string (str): OpenITI URI, e.g.,
                0768IbnMuhammadTaqiDinBaclabakki

        Example:
            >>> my_uri = URI('0768IbnMuhammadTaqiDinBaclabakki.Hadith.Shamela0009426-ara1')
            >>> my_uri.get_author_uri()
            '0768IbnMuhammadTaqiDinBaclabakki'
        """
        return self.build_uri("author")
    
        
    def normpath(func):
        """replace backslashes by forward slashes also on Windows
        This is necessary to make the doctests behave the same way
        on Windows, Mac and Unix systems"""
        def normalize(*args, **kwargs):
            r = func(*args, **kwargs)
            return re.sub(r"\\+","/", r.encode('unicode-escape').decode())
        return normalize
        

    @normpath
    def build_pth(self, uri_type=None, base_pth=None):
        """build the path to a file or folder using the OpenITI uri system

        Args:
            uri_type ((str; default: None): the uri type of the path to be returned:
                - "date" : only the date (format: 0000)
                - "author" : authorUri (format: 0255Jahiz)
                - "author_yml" : filename of the author yml file
                    (format: 0255Jahiz.yml)
                - "book": BookUri (format: 0255Jahiz.Hayawan)
                - "book_yml": filename of the book yml file
                    (format: 0255Jahiz.Hayawan.yml)
                - "version": versionURI
                    (format: 0255Jahiz.Hayawan.Shamela000245-ara1)
                - "version_yml": filename of the version yml file
                    (format: 0255Jahiz.Hayawan.Shamela000245-ara1.yml)
                - "version_file": filename of the version text file
                    (format: 0255Jahiz.Hayawan.Shamela000245-ara1.completed)
            base_pth (str): path to the root folder,
                to be prepended to the URI path

        Returns:
            pth (str): relative/absolute path

        Examples:
            >>> my_uri = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed")
            >>> my_uri.build_pth(base_pth="./master", uri_type="date")
            './master/0275AH'
            >>> my_uri.build_pth(base_pth="./master", uri_type="author")
            './master/0275AH/data/0255Jahiz'
            >>> my_uri.build_pth(base_pth="./master", uri_type="author_yml")
            './master/0275AH/data/0255Jahiz/0255Jahiz.yml'
            >>> my_uri.build_pth(base_pth="./master", uri_type="book")
            './master/0275AH/data/0255Jahiz/0255Jahiz.Hayawan'
            >>> my_uri.build_pth(base_pth="./master", uri_type="book_yml")
            './master/0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.yml'
            >>> my_uri.build_pth(base_pth="./master", uri_type="version_file")
            './master/0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed'
             >>> my_uri.build_pth(base_pth="./master", uri_type="version")
            './master/0275AH/data/0255Jahiz/0255Jahiz.Hayawan/0255Jahiz.Hayawan.Sham19Y0023775-ara1'
       """
        if base_pth is None:
            base_pth = self.base_pth

        if not uri_type:
            if self.version and self.language:
                if self.extension:
                    return self.build_pth(uri_type="version_file", base_pth=base_pth)
                else:
                    return self.build_pth(uri_type="version", base_pth=base_pth)
            elif self.title:
                return self.build_pth(uri_type="book", base_pth=base_pth)
            elif self.author:
                return self.build_pth(uri_type="author", base_pth=base_pth)
            elif self.date:
                return self.build_pth("date", base_pth)


        if uri_type == "date":
            if self.date:
                if str(self.date).endswith("AH"):
                    self.date=self.date[:-2]
                if int(self.date)%25:
                    d = "{:04d}AH".format((int(int(self.date)/25) + 1)*25)
                else:
                    d = "{:04d}AH".format(int(self.date))
                #p = os.path.join(base_pth, d)
                return os.sep.join((base_pth, d))                
            else:
                raise Exception("Error: the date component of the URI was not defined")
        elif "author" in uri_type:
            pth = os.sep.join((self.build_pth("date", base_pth), "data",
                                self.build_uri("author")))
        elif "book" in uri_type:
            pth = os.sep.join((self.build_pth("author", base_pth),
                                self.build_uri("book")))
        elif "version" in uri_type:
            if "yml" in uri_type or "file" in uri_type:
                pth = (self.build_pth("book", base_pth))
            else:
                pth = os.sep.join((self.build_pth("book", base_pth),
                                   self.build_uri("version")))
        if "yml" in uri_type or "file" in uri_type:
            return pth + os.sep + self.build_uri(uri_type)            
        else:
            return pth


def copy_file_to_URI_pth(self, in_fp, out_basepth=None):
    outfp = self.build_pth(uri_type="version", base_pth=out_basepth)
    if not os.path.exists(os.path.split(outfp)[0]):
        os.makedirs(os.path.split(outfp)[0])
    shutil.copyfile(infp, outfp)
    

if __name__ == "__main__":
    import doctest
    doctest.testmod()
    

    my_uri = "0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed"

    #URI.base_pth = "XXXX"

    t = URI(my_uri)
    print("repr(t):")
    print(repr(t))
    print("print(t):")
    print(t)
    print(t.author)
    print(t.date)
    print("URI type:", t.get_uri_type())
    print(t.build_uri("author"))
    print(t.build_pth("version"))
    print(t.build_pth("version", ""))
    print("print(t):", t)

    print("*"*30)

    u = URI()
    u.author="IbnCarabi"
    u.date="0681"
    print(u.build_uri("author"))
    print(u)

    print("*"*30)

    my_uri = URI("0255Jahiz.Hayawan.Sham19Y0023775-ara1.completed")
    print(my_uri.split_uri())
#    my_uri.extension=""
    my_uri.language=""
    print(my_uri.split_uri())
    my_uri.extension=""
    print("AN ERROR WARNING SHOULD FOLLOW: ")
    print(my_uri.build_pth(base_pth="./master", uri_type="version"))
            



