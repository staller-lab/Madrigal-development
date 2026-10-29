print("starting imports")
import pandas as pd
from ast import literal_eval
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
from tqdm import tqdm
import protfasta

import os, sys
curr_dir = os.getcwd()
import sys, os
# sys.path.append('/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/notebooks/')
sys.path.append('/global/scratch/users/claireleblanc/scripts/running_all_in_parallel')

# os.chdir('/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/notebooks/')
print(os.getcwd())
import ADpred_LambertTFs_helper

os.chdir(curr_dir)

def load_adpred_preds(working_dir, prefix):
    path = f"{working_dir}/{prefix}_ADpred_preds_dask.csv"
    adpred_preds = pd.read_csv(path, converters = dict(adpred_preds=literal_eval), index_col = 0)
    
    # Check if the first column isn't actually an index
    # i.e. has name instead of "Unnamed: 0", so undo it.
    if adpred_preds.index.name == "name":
        adpred_preds = adpred_preds.reset_index()

    
    return adpred_preds

def load_paddle_preds(working_dir, prefix):
    path = f"{working_dir}/{prefix}_Paddle_dask_preds.csv"
    if os.path.exists(path):
        paddle_preds = pd.read_csv(path, converters = dict(paddle_centers=literal_eval,
                                                paddle_preds=literal_eval), index_col = 0)
    elif os.path.exists(f"{working_dir}/{prefix}_Paddle_preds_dask.csv"):
        paddle_preds = pd.read_csv(f"{working_dir}/{prefix}_Paddle_preds_dask.csv", converters = dict(paddle_centers=literal_eval,
                                                paddle_preds=literal_eval), index_col = 0)
    else:
        path = f"{working_dir}/{prefix}_Paddle_preds.csv"
        paddle_preds = pd.read_csv(path, converters = dict(paddle_centers=literal_eval,
                                                paddle_preds=literal_eval), index_col = 0)
                                                
    # Check if the first column isn't actually an index
    # i.e. has name instead of "Unnamed: 0", so undo it.
    if paddle_preds.index.name == "name":
        paddle_preds = paddle_preds.reset_index()
        
    return paddle_preds

def load_adhunter_preds(working_dir, prefix):
    path = f"{working_dir}/{prefix}_ADHunter_preds_dask.csv"
    if os.path.exists(path):
        adhunter_preds = pd.read_csv(path, converters = dict(adhunter_centers=literal_eval,
                                            adhunter_preds=literal_eval), index_col = 0)
    elif os.path.exists(f"{working_dir}/{prefix}_ADHunter_preds.csv"):
        path = f"{working_dir}/{prefix}_ADHunter_preds.csv"
        adhunter_preds = pd.read_csv(path, converters = dict(adhunter_centers=literal_eval,
                                            adhunter_preds=literal_eval), index_col = 0)
    else: 
        path = f"{working_dir}/{prefix}_adhunter_preds.csv"
        adhunter_preds = pd.read_csv(path, converters = dict(adhunter_centers=literal_eval,
                                            adhunter_preds=literal_eval), index_col = 0)
                                            
    # Check if the first column isn't actually an index
    # i.e. has name instead of "Unnamed: 0", so undo it.
    if adhunter_preds.index.name == "name":
        adhunter_preds = adhunter_preds.reset_index()
    
    return adhunter_preds

def load_adhunter_ensemble_preds(working_dir, prefix):
    path = f"{working_dir}/{prefix}_ADhunter_ensemble_preds.csv"
    adhunter_preds = pd.read_csv(path, converters = dict(adhunter_ensemble_centers=literal_eval,
                                adhunter_ensemble_preds=literal_eval), index_col = 0)
                                
    # Check if the first column isn't actually an index
    # i.e. has name instead of "Unnamed: 0", so undo it.
    if adhunter_preds.index.name == "name":
        adhunter_preds = adhunter_preds.reset_index()

    return adhunter_preds

def load_tada_preds(working_dir, prefix):
    path = f"{working_dir}/{prefix}_TADA_preds.csv"
    if os.path.exists(path):
        tada_preds = pd.read_csv(path, converters = dict(tada_centers=literal_eval, tada_preds=literal_eval), index_col = 0)
    else:
        path = f"{working_dir}/{prefix}_TADA_preds_dask.csv"
        tada_preds = pd.read_csv(path, converters = dict(tada_centers=literal_eval, tada_preds=literal_eval), index_col = 0)
    
    # Check if the first column isn't actually an index
    # i.e. has name instead of "Unnamed: 0", so undo it.
    if tada_preds.index.name == "name":
        tada_preds = tada_preds.reset_index()
        
    return tada_preds
    
def make_adpred_intervals(preds):
    df_list = []

    for i in tqdm(range(len(preds.index))):
        # This should be the case where there are no ADs (and so we have an NaN)
        if not isinstance(preds["adpred_preds"][i], list):   # skip NaN / missing
            # print(preds["adpred_preds"][i])
            continue
        df_list.append(ADpred_LambertTFs_helper.return_pred_df(preds["adpred_preds"][i], 
                                      0.8, 
                                      10,
                                      preds["sequence"][i],
                                      preds["name"][i]))
    adpred_intervals = pd.concat(df_list)
    adpred_intervals["name"] = adpred_intervals["GeneName"]
    adpred_intervals = adpred_intervals[["name", "Start", "End"]]
    adpred_intervals["predictor"] = "ADPred"
    adpred_intervals = adpred_intervals.reset_index(drop = True)

    return adpred_intervals

def return_merged_row(name, df):
    # Only look at rows with the same name
    same_name_rows = df[df["name"] == name]
    same_name_rows = same_name_rows.sort_values(by = "Start")
    
    # Final dataframe columns
    new_starts = []
    new_ends = []
    orig_name = []
    
    # Current row's values
    curr_start = -1
    curr_end = -1
    curr_orig_name = []
    
    for i in same_name_rows.index:
        # Merge current row with next row
        if curr_end >= same_name_rows.loc[i]["Start"]:
            curr_end = max(curr_end, same_name_rows.loc[i]["End"])
        
        # Don't merge current row with next row
        else: 
            new_starts.append(curr_start)
            new_ends.append(curr_end)

            curr_orig_name = [str(c) for c in curr_orig_name]            
            
            curr_start = same_name_rows.loc[i]["Start"]
            curr_end = same_name_rows.loc[i]["End"]
    
    # Append the last values
    new_starts.append(curr_start)
    new_ends.append(curr_end)
    
    

    # curr_matching_isoforms = [c for c in curr_matching_isoforms]
    curr_orig_name = [str(c) for c in curr_orig_name]
    orig_name.append(" / ".join(curr_orig_name))
    
    # Remove the first (because it is just -1 or "")
    new_starts = new_starts[1:]
    new_ends = new_ends[1:]
    orig_name = orig_name[1:]
    
    return pd.DataFrame({"name" :name,
                         "Start": new_starts,
                        "End": new_ends
                        })
    
# def true_intervals_longer_than_5(bool_list):
#     intervals = []
#     start = None

#     for i, val in enumerate(bool_list):
#         if val:
#             if start is None:
#                 start = i
#         else:
#             if start is not None:
#                 if i - start >= 5:
#                     intervals.append((start + 26 - 1, i + 26 - 1))
#                 start = None

#     # Catch any interval that goes to the end
#     if start is not None and len(bool_list) - start >= 5:
#         intervals.append((start + 26 - 1, len(bool_list) + 26 - 1)) 

#     return intervals

def true_intervals_longer_than_5(bool_list):
    # bool list is list of trues and falses
    intervals = []
    start = None

    # We are not enumerating through the centers, i is count (basically start of AD)
    for i, val in enumerate(bool_list): 
        # If true
        if val: 
            if start is None:
                start = i # Start a new AD
        else: # If false (AD has ended) 
            # I need to somehow check that a new AD has not started within the tile length
            
            if start is not None: # if an AD already exists
                if i - start >= 5: # If we are more than 5 aa long
                    intervals.append((start, i + 53)) # Include beginning of tile to end 
                start = None

    # Catch any interval that goes to the end
    if start is not None and len(bool_list) - start >= 5:
        intervals.append((start, len(bool_list) + 53)) 

    return intervals

def make_paddle_intervals(preds):
    # At least 5 consecutive tiles with score > 4

    # Expand so that one row per tile
    paddle_preds = preds[["name", "paddle_preds", "paddle_centers"]]
    paddle_preds_expanded = paddle_preds.explode(['paddle_preds', 'paddle_centers']).reset_index(drop=True)
    paddle_preds_expanded["Start"] = paddle_preds_expanded["paddle_centers"] - 27
    paddle_preds_expanded["End"] = paddle_preds_expanded["paddle_centers"] + 26
    
    # Filter to only active tiles
    paddle_preds_expanded["active"] = paddle_preds_expanded["paddle_preds"] > 4
    
    # List of active or not
    active_lists = pd.DataFrame(paddle_preds_expanded.groupby("name")["active"].agg(list)).reset_index()
    
    # Return intervals with at least 5 consecutive tiles
    active_lists["intervals"] = active_lists["active"].apply(lambda lst: true_intervals_longer_than_5(lst))

    
    active_lists["num_intervals"] = [len(_) for _ in active_lists["intervals"]]
    
    # Keep rows with predicted AD
    final_preds = active_lists[active_lists["num_intervals"] > 0]
    final_preds_expanded = final_preds[["name", "intervals"]].explode("intervals")
    
    # Formatting
    final_preds_expanded["Start"] = [_[0] for _ in final_preds_expanded["intervals"]]
    final_preds_expanded["End"] = [_[1] for _ in final_preds_expanded["intervals"]]
    final_preds_expanded = final_preds_expanded[["name", "Start", "End"]].reset_index(drop=True)

    # Merging intervals that overlap on the same protein - ADDED, will see if this works
    dfs = []
    i = 0
    for name in final_preds_expanded["name"].unique():
        dfs.append(return_merged_row(name, final_preds_expanded))

    if len(dfs) > 0: 
        merged_active_tile_coords = pd.concat(dfs)
        merged_active_tile_coords = merged_active_tile_coords.reset_index(drop = True)
        paddle_intervals = merged_active_tile_coords
        paddle_intervals["predictor"] = "PADDLE"
        return paddle_intervals
    else: 
        return None

def make_adhunter_intervals(preds):
    # Expanding so one row per tiles
    ADHunter_preds_expanded = preds[["name", "adhunter_centers", "adhunter_preds"]].explode(['adhunter_centers', 'adhunter_preds']).reset_index(drop=True)
    ADHunter_preds_expanded["Start"] = ADHunter_preds_expanded["adhunter_centers"] - 20
    ADHunter_preds_expanded["End"] = ADHunter_preds_expanded["adhunter_centers"] + 20
    
    # Filtering to active rows
    active_preds = ADHunter_preds_expanded[ADHunter_preds_expanded["adhunter_preds"] > 94031] # Use 80% threshold from Gcn4 paper
    active_tile_coords = active_preds[["name", "Start", "End"]]
    active_tile_coords.reset_index(inplace= True, drop=True)
    
    # Merging itnervals on same protein
    dfs = []
    i = 0
    for name in active_tile_coords["name"].unique():
        dfs.append(return_merged_row(name, active_tile_coords))
    
    if len(dfs) > 0: 
        merged_active_tile_coords = pd.concat(dfs)
        merged_active_tile_coords = merged_active_tile_coords.reset_index(drop = True)
        adhunter_intervals = merged_active_tile_coords
        adhunter_intervals["predictor"] = "ADHunter"
        return adhunter_intervals
    else: 
        return None

def make_adhunter_ensemble_intervals(preds):
    # Expanding so one row per tiles
    ADHunter_preds_expanded = preds[["name", "adhunter_ensemble_centers", "adhunter_ensemble_preds"]].explode(['adhunter_ensemble_centers', 'adhunter_ensemble_preds']).reset_index(drop=True)
    ADHunter_preds_expanded["Start"] = ADHunter_preds_expanded["adhunter_ensemble_centers"] - 27
    ADHunter_preds_expanded["End"] = ADHunter_preds_expanded["adhunter_ensemble_centers"] + 26
    
    # Filtering to active rows
    # Threshold is mean of harmonized dataset + std (0.4441)
    active_preds = ADHunter_preds_expanded[ADHunter_preds_expanded["adhunter_ensemble_preds"] > 0.4441]
    active_tile_coords = active_preds[["name", "Start", "End"]]
    active_tile_coords.reset_index(inplace= True, drop=True)
    
    # Merging itnervals on same protein
    dfs = []
    i = 0
    for name in active_tile_coords["name"].unique():
        dfs.append(return_merged_row(name, active_tile_coords))

    # What if there are no ADs?? Need to address that case
    if len(dfs) > 0: 
        merged_active_tile_coords = pd.concat(dfs)
        merged_active_tile_coords = merged_active_tile_coords.reset_index(drop = True)
        adhunter_intervals = merged_active_tile_coords
        adhunter_intervals["predictor"] = "ADHunter_ensemble"
        return adhunter_intervals
    else: 
        return None

def make_tada_intervals(preds):
    # Expanding so one row per tiles
    tada_preds_expanded = preds[["name", "tada_centers", "tada_preds"]].explode(['tada_centers', 'tada_preds']).reset_index(drop=True)
    tada_preds_expanded["Start"] = tada_preds_expanded["tada_centers"] - 20
    tada_preds_expanded["End"] = tada_preds_expanded["tada_centers"] + 20
    
    # Filtering to active rows
    active_preds = tada_preds_expanded[tada_preds_expanded["tada_preds"] > 0.4]
    active_tile_coords = active_preds[["name", "Start", "End"]]
    active_tile_coords.reset_index(inplace= True,drop=True)
    
    # Merging intervals on same protein
    dfs = []
    i = 0
    for name in active_tile_coords["name"].unique():
        dfs.append(return_merged_row(name, active_tile_coords))

    # Check if there are any predicted activation domains
    if len(dfs) > 0: 
        merged_active_tile_coords = pd.concat(dfs)
        merged_active_tile_coords = merged_active_tile_coords.reset_index(drop = True)
        tada_intervals = merged_active_tile_coords
        tada_intervals["predictor"] = "TADA"
        return tada_intervals
    else:
        return None

def get_composition_intervals(working_dir, prefix):
    composition_preds = pd.read_csv(f"{working_dir}/{prefix}_s_001_lcc_VP16_lch_006_ucc_-08_uch_CITED2_lcs1_inf_lcs2_000_lcs1_inf_ucs2_inf_comp_WFL_tl_039_ws_001_ps1_Charge_ps2_AllHydros")

    composition_preds["name"] = composition_preds["GeneName"]
    composition_intervals = composition_preds[["name", "Start", "End"]]
    composition_intervals["predictor"] = "Composition"
    return composition_intervals

def combine_intervals(name, preds, all_models, num_models):
    all_models_rows = all_models[all_models["name"] == name]
    TF_length = preds[preds["name"] == name]["len"].iloc[0].astype(int)
    
    if len(all_models_rows) > 0:
        preds = []

        for i in range(len(all_models_rows)):
            row_preds = np.zeros(TF_length)
            row = all_models_rows.iloc[i]
            if row['Start'] < 0: 
                print("ERROR")
            row_preds[row["Start"]:row["End"]] = 1
            preds.append(row_preds)

        all_models_rows["preds"] = preds
        if (sum(all_models_rows["preds"]) > 6).any():
            print(all_models_rows, sum(all_models_rows["preds"]))
        return sum(all_models_rows["preds"]) / num_models # FIX DIVISION BY 5!!

    else:
        return np.zeros(TF_length)

def read_fasta(file):
    with open(file, 'r') as f:
        lines = f.readlines()
    names = []
    seqs = []
    seq = ""
    for line in lines: 
        if line.startswith('>'): 
            names.append(line.replace(">", "").strip())
            if len(names) > 1:
                seqs.append(seq)
                seq = ""
        else:
            seq += line.strip()
    
    seqs.append(seq)

    return pd.DataFrame({'name' : names, 'sequence' : seqs})

def main(args):
    working_dir = args.d
    prefix = args.p
    output_name = args.o

    # Which of the models to combine
    adhunter = args.ah
    adhunter_ensemble = args.ae
    adpred = args.ap
    tada = args.t
    composition = args.c
    paddle = args.pa

    num_predictors = adhunter + adhunter_ensemble + adpred + tada + composition + paddle
    print(num_predictors)
    print(f"Running analysis for {prefix}")

    # Read in sequences
    preds = read_fasta(f"{working_dir}/{prefix}.fasta")

    # The merges get weird if there are duplicates in the fasta file - does not fix the bug
    preds = preds.drop_duplicates(['name', 'sequence'])
    print(preds.columns)
    
    # Load in predictions
    if adhunter:
        adhunter_preds = load_adhunter_preds(working_dir, prefix)
        adhunter_preds = adhunter_preds.drop_duplicates(['name', 'sequence'])
        print(f"Loaded ADHunter")
        preds = preds.merge(adhunter_preds, on=['name', 'sequence'], how='left')
        preds = preds.reset_index(drop=True)
        print(preds.columns)

    if adhunter_ensemble: 
        adhunter_ensemble_preds = load_adhunter_ensemble_preds(working_dir, prefix)
        adhunter_ensemble_preds = adhunter_ensemble_preds.drop_duplicates(['name', 'sequence'])
        print(f"Loaded ADHunter ensemble")

        # Merging preds 
        preds = preds.merge(adhunter_ensemble_preds, on=['name', 'sequence'], how='left')
        preds = preds.reset_index(drop=True) 
        print(preds.columns)
    
    if tada: 
        tada_preds = load_tada_preds(working_dir, prefix)
        tada_preds = tada_preds.drop_duplicates(['name', 'sequence'])
        print(f"Loaded TADA")

        # Merging preds 
        preds = preds.merge(tada_preds, on=['name', 'sequence'], how='left')
        preds = preds.reset_index(drop=True) 
        print(preds.columns)
    
    if adpred: 
        adpred_preds = load_adpred_preds(working_dir, prefix)
        adpred_preds = adpred_preds.drop_duplicates(['name', 'sequence'])
        print(f"Loaded ADPred")

        # Merging preds 
        preds = preds.merge(adpred_preds, on=['name', 'sequence'], how='left')
        preds = preds.reset_index(drop=True) 
        print(preds.columns)

    if paddle: 
        paddle_preds = load_paddle_preds(working_dir, prefix)
        paddle_preds = paddle_preds.drop_duplicates(['name', 'sequence'])
        print(f"Loaded PADDLE")

        # Merging preds
        preds = preds.merge(paddle_preds, on=['name', 'sequence'], how='left')
        preds = preds.reset_index(drop=True) 
        print(preds.columns)

    preds["len"] = preds['sequence'].str.len()
    print(f"Merged predictions")

    # Get activation domains
    all_models = None

    if adhunter: 
        adhunter_intervals = make_adhunter_intervals(preds)
        print(f"Made ADhunter intervals")
        
        if adhunter_intervals is not None:
            all_models = adhunter_intervals

    if adhunter_ensemble: 
        adhunter_ensemble_intervals = make_adhunter_ensemble_intervals(preds)
        print(f"Made ADhunter ensemble intervals")
        
        # Concat intervals
        if adhunter_ensemble_intervals is not None: # Checking that there are activation domains
            if all_models is None: 
                all_models = adhunter_ensemble_intervals
            else:
                all_models = pd.concat([all_models, adhunter_ensemble_intervals])
    
    if tada: 
        tada_intervals = make_tada_intervals(preds)
        print(f"Made TADA intervals")

        # Concat intervals
        if tada_intervals is not None: 
            if all_models is None: 
                all_models = tada_intervals
            else:
                all_models = pd.concat([all_models, tada_intervals])
    
    if adpred: 
        adpred_intervals = make_adpred_intervals(preds)
        print(f"Made ADPred intervals")

        # Concat intervals
        if adpred_intervals is not None: 
            if all_models is None: 
                all_models = adpred_intervals
            else:
                all_models = pd.concat([all_models, adpred_intervals])
    
    if paddle: 
        paddle_intervals = make_paddle_intervals(preds)
        print(paddle_intervals)
        print(f"Made PADDLE intervals")

        # Concat intervals
        if paddle_intervals is not None: 
            if all_models is None: 
                all_models = paddle_intervals
            else:
                all_models = pd.concat([all_models, paddle_intervals])
    
    if composition: 
        composition_intervals = get_composition_intervals(working_dir, prefix)
        print(f"Made composition intervals")

        # Concat intervals
        if composition_intervals is not None: 
            if all_models is None: 
                all_models = composition_intervals
            else:
                all_models = pd.concat([all_models, composition_intervals])


    # all_models = pd.concat([adhunter_intervals, tada_intervals, adpred_intervals, composition_intervals, paddle_intervals])

    all_models["Start"] = all_models["Start"].astype(int)
    all_models["End"] = all_models["End"].astype(int)
    
    preds["combined_preds"] = preds["name"].apply(lambda id: combine_intervals(id, preds, all_models, num_predictors))

    # This is to get individual intervals
    all_models_intervals = all_models.groupby(['name', 'predictor']).apply(lambda x: list(zip(x['Start'], x['End']))).unstack('predictor')
    all_models_intervals.columns = [f"{col}_intervals" for col in all_models_intervals.columns]
    all_models_intervals = all_models_intervals.reset_index()
    print(all_models_intervals)
    print("Made all model intervals")
    
    preds = preds.merge(all_models_intervals, on='name', how='left')
    print(f"Combined intervals")

    data = []
    for i in preds.index:
        sequence = preds.loc[i, "sequence"]
        name = preds.loc[i, "name"]
        
        intervals = []
        interval_cols = []

        for cname in ['ADHunter_intervals', 
                      'TADA_intervals', 'ADPred_intervals', 'PADDLE_intervals', 
                      'ADHunter_ensemble_intervals', 'Composition_intervals']:
            if cname in preds.columns: 
                intervals.append(preds.loc[i, cname]) 
                interval_cols.append(cname.lower())

        list_columns = []
        out_col_names = []
        for cname in ['adhunter_centers', 'adhunter_preds','tada_centers', 
                      'tada_preds', 'adpred_preds', 'paddle_centers',
                      'paddle_preds', 'adhunter_ensemble_centers', 'adhunter_ensemble_preds', 
                      'adhunter_ensemble_uncertainty', 'combined_preds']:
            if cname in preds.columns: 
                out_col_names.append(cname)
                ls = preds.loc[i, cname]
                if isinstance(ls, list) or isinstance(ls, np.ndarray):
                    ls = "[" + ",".join(str(x) for x in ls) + "]"
                else: 
                    ls = []
                list_columns.append(ls)

        data.append([name, sequence] + list_columns + intervals)

    out_df = pd.DataFrame(data, columns=['name', 'sequence'] + out_col_names + interval_cols)
    out_df.to_csv(f"{working_dir}/{output_name}", encoding='utf-8')

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Prefix to the prediction files", type=str)
    parser.add_argument("-d", help="Working directory (containing predictions)", type=str)
    parser.add_argument("-o", help="output name", type=str)

    parser.add_argument("-ah", action='store_true', help="Whether to include ADhunterLite in combined preds")
    parser.add_argument("-ae", action='store_true', help="Whether to include ADhunterEnsemble in combined preds")
    parser.add_argument("-ap", action='store_true', help="Whether to include ADpred in combined preds")
    parser.add_argument("-t", action='store_true', help="Whether to include TADA in combined preds")
    parser.add_argument("-pa", action='store_true', help="Whether to include Paddle in combined preds")
    parser.add_argument("-c", action='store_true', help="Whether to include composition in combined preds")

    args = parser.parse_args()
    main(args)
    
