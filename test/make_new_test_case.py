import os
import shutil
import re

def make_new_test_case(new_author_uri,
                       base_path = "25-years-folders/0025AH/data",
                       template="0000Template",
                       overwrite=True):
    """Make a copy of all files in an existing test case folder
    changing all file names and yml files accordingly."""
    
    template_pth = os.path.join(base_path, template)
    new_author_uri_pth = os.path.join(base_path, new_author_uri)
    
    # remove folder if it already exists
    
    if overwrite:
        try:
            shutil.rmtree(new_author_uri_pth)
        except:
            pass

    # copy template folder and all its contents:
    shutil.copytree(template_pth, new_author_uri_pth)


    # change filenames and URIs in yml files:
    for fn in os.listdir(new_author_uri_pth):
        fp = os.path.join(new_author_uri_pth, fn)
        if fn.endswith(".yml"):
            new_fp = re.sub(template, new_author_uri, fp)
            os.rename(fp, new_fp)
            with open(new_fp, mode="r", encoding="utf-8") as file:
                text = file.read()
                text = re.sub(template, new_author_uri, text)
            with open(new_fp, mode="w", encoding="utf-8") as file:
                file.write(text)
        elif os.path.isdir(fp):
            book_uri = os.path.basename(fp)
            book_title = book_uri.split(".")[-1]
            print(book_uri)
            new_book_uri = new_author_uri+"."+book_title
            book_folder = os.path.join(new_author_uri_pth, new_book_uri)
            os.rename(fp, book_folder)
            for f in os.listdir(book_folder):
                fp = os.path.join(book_folder, f)
                if f == book_uri + ".yml":
                    new_fp = os.path.join(book_folder, new_book_uri + ".yml")
                    os.rename(fp, new_fp)
                    with open(new_fp, mode="r", encoding="utf-8") as file:
                        text = file.read()
                        text = re.sub(book_uri, new_book_uri, text)
                    with open(new_fp, mode="w", encoding="utf-8") as file:
                        file.write(text)
                elif "-" in f:
                    version_id = re.findall("(?<=\.)[a-zA-Z0-1]+-[a-z]{3}\d+", f)[0]
                    print(version_id)
                    n = re.findall("\d+(?=-)", version_id)[0]
                    new_n = re.findall("\d+", new_author_uri)[0]
                    old_version_uri = "{}.{}".format(book_uri, version_id)
                    new_version_uri = "{}.{}".format(new_book_uri, version_id)
                    new_version_uri = re.sub(n, "{:03d}".format(int(new_n)), new_version_uri)
                    if f.endswith(".yml"):
                        new_fp = os.path.join(book_folder, new_version_uri+".yml")
                        os.rename(fp, new_fp)
                        with open(new_fp, mode="r", encoding="utf-8") as file:
                            text = file.read()
                            text = re.sub(old_version_uri, new_version_uri, text)
                        with open(new_fp, mode="w", encoding="utf-8") as file:
                            file.write(text)
                    else:
                        new_fp = os.path.join(book_folder, new_version_uri)
                        os.rename(fp, new_fp)

    # copy new test case to release_structure folder:
    dst = os.path.join("release_structure", new_author_uri)
    if os.path.exists(dst) and overwrite:
        shutil.rmtree(dst)
    if not os.path.exists(dst):
        shutil.copytree(new_author_uri_pth, dst)

    # copy new test case to flat_structure folder:
    for root, dirs, files in os.walk(new_author_uri_pth):
        for fn in files:
            print(fn)
            if fn.startswith("00"):
                fp = os.path.join(root, fn)
                shutil.copyfile(fp, os.path.join("flat_structure", fn))


input()
    
            
#make_new_test_case("0011LongWordInAuthorYml")
#make_new_test_case("0012NoIndentationInAuthorYml")
#make_new_test_case("0013GenreTest")
#make_new_test_case("0014MissingColonInAuthorYml")
#make_new_test_case("0015EmptyAuthorYml")
#make_new_test_case("0016MissingAuthorYml")
#make_new_test_case("0017MissingBookYml")
#make_new_test_case("0018MissingVersionYml")
make_new_test_case("0020TEST")



