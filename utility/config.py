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

# path to the output folder:
output_path = "./output/"

# path to the output files (default: in the folder at output_path)
meta_tsv_fp = None
meta_yml_fp = None
meta_json_fp = None
meta_header_fp = None

# List of lists (description, run_id on server):  
passim_runs = [['October 2017 (V1)', 'passim1017'],
               ['February 2019 (V2)', 'passim01022019'],
               ['May 2019 (Aggregated)', 'aggregated01052019'],
               ['February 2020', 'passim01022020']]

# Set to True to allow the script to make changes to yml files without asking:
silent = False  # True/False