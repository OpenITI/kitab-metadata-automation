# RESTORED DEFAULTS:

# Path to the input folder:
corpus_path = "/home/admin-kitab/Documents/OpenITI/RELEASE_git/working_dir/AH_repos/"
# list of folder names to be excluded from metadata generation:
exclude = (["OpenITI.github.io", "Annotation", "maintenance", "i.mech00",
            "i.mech01", "i.mech02", "i.mech03", "i.mech04", "i.mech05",
            "i.mech06", "i.mech07", "i.mech08", "i.mech09", "i.logic",
            "i.cex", "i.cex_Temp", "i.mech", "i.mech_Temp", ".git", "8001AH"])

# Set to True if the data is in 25-year folders, False if they are not:
data_in_25_year_repos = True  # True/False

# Set to True if the script needs to check completeness of the yml files:
perform_yml_check = False  # True/False

# Set to True if the script needs to update the token counts in the yml files:
check_token_counts = False  # True/False

# Set to True if the script needs to include character length in the yml files:
incl_char_length = True  # True/False

# Split title and author data in Arabic and Latin script into separate columns:
split_ar_lat = True # True/False

# path to the output folder:
output_path = "./output"

# Use this path instead of the `corpus_path` for text and yml files in output metadata:
# E.g., "https://raw.githubusercontent.com/OpenITI", ".."
output_files_path = ""

# remove these folders from the path:
remove_from_path = ["25Y_repos", "25Y_repos_[A-Z]{3}"] 

# path to the output files (default: in the folder at output_path)
meta_tsv_fp = None
meta_yml_fp = None
meta_json_fp = None
meta_header_fp = None

# List of lists (description, run_id on server):  
passim_runs = [['2017 (V1)', 'passim1017'],
               ['2019.1.1', 'passim01022019'],
#               ['May 2019 (Aggregated)', 'aggregated01052019'],
               ['2020.1.2', 'passim01022020'],
               ['2020.2.3', 'passim01102020'],
               ['2020.2.3 (Aggregated)', 'aggregated01102020'],
               ['2021.1.4', 'passim01022021'],
               ['2021.1.4 (Aggregated)', 'aggregated01022021'],
#               ['July 2022', 'passim01072022'],
#               ['2021.2.5', 'passim01102021'],
               ['2021.2.5', '2021.2.5-pairwise'],
#               ['2022.1.6', 'passim01102022'],
               ['2022.1.6', '2022.1.6-pairwise'],
               ['2023.1.8', '2023.1.8-pairwise']]

# Set to True to allow the script to make changes to yml files without asking:
silent = True  # True/False
