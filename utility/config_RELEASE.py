corpus_path = "../RELEASE/data_temp"
exclude = (["OpenITI.github.io", "Annotation", "maintenance", "i.mech00",
            "i.mech01", "i.mech02", "i.mech03", "i.mech04", "i.mech05",
            "i.mech06", "i.mech07", "i.mech08", "i.mech09", "i.logic",
            "i.cex", "i.cex_Temp", "i.mech", "i.mech_Temp", ".git"])
data_in_25_year_repos = False
perform_yml_check = False
check_token_counts = False
incl_char_length = True
output_path = "./output/"
meta_tsv_fp = None
meta_yml_fp = None
meta_json_fp = None
meta_header_fp = None
passim_runs = [['October 2017 (V1)', 'passim1017'],
               ['February 2019 (V2)', 'passim01022019'],
               ['May 2019 (Aggregated)', 'aggregated01052019'],
               ['February 2020', 'passim01022020']]
silent = False
