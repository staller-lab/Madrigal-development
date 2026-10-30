

00_Downloading_all_InterPro-superfamilies.ipynb: Gets seqences from uniprot with TF DBDs. Used Lambert 2018 paper’s list of DBD families. Writes sequences to data/interpro_seq_uniprotids.csv and to data/interpro_uniprot_evid_1_2.fasta. 

01_Input_data_clusers.ipynb: Loads both uniprot sequences and y1000+ sequences. We used all y1000+ orthogroups that contained at least one S. cerevisiae DBD. 

make_parrot_input.ipynb: Loads non_cl_seqs_{prefix}_combined_filtered.csv and ../predictions/combined_preds/y1000_filtered_{prefix}_combined.csv. These are the predictions from the y1000+ and the uniprot sequences. prefix indicates whether any models are left out. Final model used "all_six" as prefix. Creates the final parrot input. Also filters out the representative cluster sequences for the full length TFsin the test set of Sanborn that we use to evaluate our model. This final filtering step occurs here because we added these test sequences later. 

loading_and_filtering_yeast_preds.ipynb: Creates ../predictions/combined_preds/y1000_filtered_{prefix}_combined.csv. Loads sequence names from cl_seqs_filtered.txt. Extract names and corresponding sequences from y1000+ project TF predictions. 

checking_seq_sets.ipynb: There were some differences between what we predicted and 

## Code not used to create input

These scripts were used for debugging, exploration, etc. but not necessary for creating the final input. 

- finding_missing_paddle_preds.ipynb
- prep_regression_input.ipynb: Looked at having a continuous input instead of just the fraction of predictors
- regression_input_explore.ipynb: Looked at having a continuous input instead of just the fraction of predictors
- 