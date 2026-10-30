# Madrigal: Multi-model Activation Domain Recurrent-neural-network Inferring Grouped Activity Labels

Madrigal is a bidirectional LSTM (trained with PARROT) that takes a protein sequence of any length and predicts, for each residue, the fraction of six activation domain (AD) predictors that call that residue part of an AD. The six predictors are:

- **PADDLE** (doi: 10.7554/eLife.68068) 
- **TADA** (doi: 10.1038/s41586-024-07707-3) 
- **ADpred** (doi: 10.1016/j.molcel.2020.04.020) 
- **ADhunterLite** (doi: 10.1371/journal.pgen.1012069) 
- **ADhunterEnsemble** (doi: 10.1186/s13059-026-04269-7)
- **Kotha Composition Model** (doi: 10.1093/genetics/iyad131) 
---

To run Madrigal online, visit: https://www.madrigal-predictor.net

To run Madrigal as a python package, visit: https://pypi.org/project/madrigal-predictor/

This repository contains the code used to create and evaluate Madrigal. If you run into any questions or issues with the code, please email claireleblanc [at] berkeley.edu or submit a github issue. 

---

## Pipeline overview

| Step | What happened | What code was used |
|---|---|---|
| 1 | Collected sequences from Y1000+ yeast, PlantTFDB, and InterPro (DBD families), then de-duplicated | `notebooks/00_Downloading_all_InterPro-superfamilies.ipynb` |
| 2 | Filter the sequences based on length and disorder. Length filter: 53 aa (PADDLE minimum) to 1,442 aa (99th percentile). Disorder filter: at least 20% predicted disorder | `notebooks/01_Input_data_clusters.ipynb` |
| 3 | Clustered with `mmseqs cluster` at 75% identity, kept one representative per cluster | `notebooks/02_Input_data_clusters_with_mimum_sequence_identity.ipynb` |
| 5 | Removed training sequences similar to test screen sequences | `notebooks/03_Generating_test_set.ipynb` |
| 6 | Removed training sequences similar to synthetic sequences | `notebooks/04_Removing_synthetics_from_training.ipynb` |
| 7 | Split sequences into chunks of 1,000. This was to speed up the predictions and avoid memory errors. | `notebooks/05_split_seqs_into_smaller_files.ipynb` | 
| 8 | Ran all six predictors on the training and test sequences |`bash_scripts/run_CL_dask_all_split.sh`, `bash_scripts/run_CL_dask_all_split_on_missing.sh`, `bash_scripts/run_adhunter_ensemble_gpu.sh`, |
| 9 | Combined all six predictors into a consensus prediction (the fraction of residues that each predictor predicts as part of an activation domain) | `bash_scripts/make_consensus.sh`, To combine separate parts: `head -n 1 pt1_combined_all_six.csv > non_cl_seqs_all_six_combined.csv`, `tail -q -n +2 pt*_combined_all_six.csv >> non_cl_seqs_all_six_combined.csv` |
| 10 | Filter the sequences to make sure we have the correct sets. Reconciles the predicted sequences with the final 230,302-sequence training set. It removes 2,492 sequences that were left over from before the synthetics filter was added, and it splits the remaining sequences into Y1000+ (CL) sequences (95,634) and non-CL sequences (134,655). | `notebooks/checking_seq_sets.ipynb` |
| 11 | Pulls the predictions for the filtered Y1000+ sequences | `loading_and_filtering_yeast_preds.ipynb` |
| 12 | Prepare input for parrot model training. Combines y1000 and non-y1000 predictions and writes the PARROT input files. Also removes PADDLE representative sequences of clusters that contain yeast TFs used in our test set. We added these sequences after original versions of the model, so the clusters are removed here. | `make_parrot_input.ipynb` |
| 12 | Trains the final Madrigal model on all six predictors | `train_parrot_all_six.sh` | 
| 13 | Evaluate both regression and classification on our held out test-set | `predict_parrot_all_six.sh`, `notebooks/combined_precision_recall_per_residue.ipynb`, `notebooks/regression/evaluate_parrot.ipynb`, `notebooks/regression/synthetics_and_parrotipynb` | 

**Overlap filter used in steps 6 and 7:** a training sequence was removed if it covered more than 90% of a test or synthetic sequence at 30% or higher sequence identity (`mmseqs search`).

---

## Step details

### 1. Input sequences

- **Y1000+ yeast** (n = 172,854): homologs of *S. cerevisiae* TFs.
  - File: `notebooks/data/cl_seqs.fasta`
- **PlantTFDB** (n = 310,656):
  - File: `notebooks/data/PlantTFDB-all_TF_pep.fas`
- **InterPro** (n = 137,436):
  1. Took DBD families from Lambert et al. 2018, keeping families with more than one known human TF and dropping duplicates and the "unknown" category.
  2. Mapped each family to an InterPro domain or superfamily. The mapping is tracked in a Google Sheet.
  3. Pulled UniProt sequences with evidence levels 1 and 2.
  - File: `data/interpro_uniprot_evid_1_2.fasta`

### 8, 9. Running predictors and building consensus

1. **Tiling:** each protein was tiled with a 1 aa step at each predictor's input length:
   - PADDLE and ADhunterEnsemble: 53 aa
   - TADA and ADhunterLite: 40 aa
   - ADpred: 30 aa
2. **Calling AD residues:** a residue counts as an AD residue for a given predictor if it falls in any tile that passes that predictor's published threshold.
3. **Consensus:** the consensus value for each residue is the fraction of predictors that call it.

### 12. Training

- **Model:** PARROT bidirectional LSTM, regression task, one-hot encoded input.
- **Settings:** 1 hidden layer, hidden vector size 10, learning rate 0.001.
- **Data split:** random 70 / 15 / 15 train / validation / test.
- **Stopping:** training stopped after validation performance plateaued for 10 epochs.

Models trained:

- The all-six model.
- Leave-one-out models, each dropping one predictor.

Before training, we removed the 17 full-length TFs (*Saccharomyces* orthologs plus P07249) that are in the PADDLE test set. These sequences were not part of the original test set, but they were added after we realized that because they were not used to train PADDLE and we could use them in our test set. 

### 13. Evaluation

- **Classification:** residue-level PRC and ROC on full-length TFs with known ADs.

  | Dataset | Full-length TFs | Total Residues
  |---|---|---|
  | Yeast | 16 | 12,981
  | Fly | 49 | 33,772
  | Plant | 355 | 101,141
  | Human | 25 | 13,895

- **Regression:** Pearson and Spearman correlation against screen tile activities. When a tile was longer than a predictor's input, we scored the tile's sub-tiles and took the mean or the max.

These sequences were used to test the regressive power of our trained model. There is some overlap with the sequences/screens that we used to train the classification model (see below). 

- **ARF** (Morffy et al.): Supplementary Table S3.
- **Sanborn**: sub-libraries D and E only. Sub-libraries A and B were used to train PADDLE.
- **Hummel**: `hummel_ratio_20230530`. This set was included in the overlap filter but was not used for final evaluation, because ADhunterEnsemble was trained on it.
- **Erkine / Ravarani**: supplementary tables of measured activities.
- **Arnold**: fold change ≥ 1.5 and P ≤ 1e-5, using tables EV2, EV4, EV5, and EV6.
- **DelRosso**: 25 randomly chosen TFs out of 1,241. We used a subset so that most human TFs stay in the training data.
- **Sog1**
- **Synthetics**

Activities for the test tiles are in `notebooks/regression/screen_test_seqs_with_activities.csv`.

> **Note on DelRosso:** a merge bug mapped about 1,200 tiles to the 25 DelRosso TFs instead of the correct ~800. All ~1,200 tiles were used when removing training sequences, which removed roughly 3,000 extra training sequences. We did not redo the clustering, because the predictions had already been run. The activities file above uses the correct 804 tiles.

---

## Key files

### Final PARROT inputs, in `compressed_data`

| File | Contents |
|---|---|
| `parrot_input_all_six.tsv.gz` | Input for the final model (230,289 sequences) |
| `parrot_input_no_<predictor>.tsv.gz` | Inputs for the leave-one-out models |

---
