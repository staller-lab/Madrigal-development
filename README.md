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
- **Synthetics**

Activities for the test tiles are in `notebooks/regression/screen_test_seqs_with_activities.csv`.

> **Note on DelRosso:** a merge bug mapped about 1,200 tiles to the 25 DelRosso TFs instead of the correct ~800. All ~1,200 tiles were used when removing training sequences, which removed roughly 3,000 extra training sequences. We did not redo the clustering, because the predictions had already been run. The activities file above uses the correct 804 tiles.

---

## Software environments

Model development ran across two machines: the notebooks on macOS, and the
predictor runs and model training on the Berkeley Savio cluster. The
environment files are in `envs/`, exported in two forms — `*_from-history.yml`
lists only the packages that were explicitly requested and is the portable file
to install from, while `*_full.yml` records the complete solved environment and
is the provenance record.

Create any of them with, for example:

```
conda env create -f envs/parrot_fixed_from-history.yml
```

| Environment | Machine | Used for |
|---|---|---|
| `basic_env_*.yml` | macOS Tahoe 26.6.2 (Apple M3) | All notebooks in `notebooks/` — sequence collection, filtering, clustering, test-set construction and evaluation |
| `new_dask_*.yml` | Savio | Running five of the six predictors (`bash_scipts/run_CL_dask_*.sh`) |
| `adhunter_esm_*.yml` | Savio, GPU | ADhunterEnsemble (`bash_scipts/run_adhunter_ensemble_gpu.sh`) |
| `parrot_fixed_*.yml` | Savio, GPU | PARROT training and prediction (`bash_scipts/train_parrot_*.sh`, `predict_parrot_*.sh`) |
| `dask_v3_*.yml` | Savio | Working copy of the predictor environment, with Dask added |

### Notebooks — `basic_env` (macOS)

| Package | Version |
|---|---|
| python | 3.13.2 |
| numpy | 2.2.5 |
| pandas | 2.2.3 |
| scipy | 1.15.3 |
| scikit-learn | 1.6.1 |
| scikit-image | 0.25.2 |
| statsmodels | 0.14.4 |
| matplotlib | 3.10.0 |
| seaborn | 0.13.2 |
| biopython | 1.85 |
| metapredict | 3.0.1 |
| localCIDER | 0.1.21 |
| markovify | 0.9.4 |
| editdistance | 0.8.1 |
| python-levenshtein | 0.27.1 |
| torch | 2.11.0 |
| pytorch-lightning | 2.6.1 |
| logomaker | 0.8 |
| upsetplot | 0.9.0 |
| mygene | 3.2.2 |

### Running five predictors — `new_dask` (Savio)

| Package | Version |
|---|---|
| python | 3.10.8 |
| **ADpred** | **1.3.1** |
| tensorflow | 2.10.0 |
| keras | 2.10.0 |
| pytorch | 2.0.0 (CPU build) |
| pytorch-lightning | 1.7.7 |
| torchmetrics | 0.11.4 |
| dask | 2025.5.1 |
| dask-jobqueue | 0.9.0 |
| distributed | 2025.5.1 |
| numpy | 1.26.4 |
| pandas | 2.0.0 |
| scipy | 1.14.1 |
| scikit-learn | 1.2.2 |
| statsmodels | 0.14.4 |
| matplotlib-base | 3.9.2 |
| seaborn | 0.13.2 |
| biopython | 1.84 |
| numba | 0.60.0 |
| shap | 0.46.0 |
| localCIDER | 0.1.21 |
| protfasta | 0.1.15.2 |
| alphapredict | 1.3.0 |
| ipyparallel | 8.6.1 |

Of the six predictors, only ADpred was installed as a package. PADDLE, TADA,
ADhunterLite and the Kotha composition model were run from the source released
with their respective publications, cited above, and carry no version numbers.

`dask_v3` is a working copy of this environment with Dask added; its export is
included for completeness.

### ADhunterEnsemble — `adhunter_esm` (Savio, GPU)

Run on a GPU with `--use-gpu`; the CUDA version here matches the `cuda/11.8.0`
module loaded by the batch script.

| Package | Version |
|---|---|
| python | 3.8.16 |
| **fair-esm** | **2.0.0** |
| pytorch | 2.0.0 |
| pytorch-cuda | 11.8 |
| pytorch-lightning | 1.7.7 |
| torchmetrics | 0.7.3 |
| torchvision | 0.15.0 |
| numpy | 1.24.4 |
| pandas | 2.0.1 |
| scipy | 1.10.1 |
| scikit-learn | 1.3.2 |
| statsmodels | 0.14.1 |
| matplotlib | 3.7.1 |
| seaborn | 0.12.2 |
| biopython | 1.81 |
| diamond | 2.1.16 |

### Training and prediction — `parrot_fixed` (Savio, GPU)

Training used one NVIDIA GTX 2080 Ti.

| Package | Version |
|---|---|
| python | 3.9.23 |
| **idptools-parrot** | **1.7.5** |
| torch | 2.8.0 |
| pytorch-lightning | 2.6.0 |
| torchmetrics | 1.8.2 |
| numpy | 2.0.2 |
| scipy | 1.13.1 |
| scikit-learn | 1.6.1 |
| pandas | 2.3.3 |
| matplotlib | 3.9.4 |
| seaborn | 0.13.2 |
| metapredict | 3.0.1 |
| protfasta | 0.1.15.2 |

The training and prediction scripts activate a copy of `parrot_fixed` under a
shared project directory; `sanjana_parrot_fixed_full.yml` is its export, and
its package versions match `parrot_fixed_full.yml`.

### A note on versions

These environments were exported after the analyses were complete, so some
package versions are newer than those used at the time; where an executed
notebook's own metadata differs, the notebook metadata reflects the version
that produced the published result.

The released predictor is distributed as
[madrigal-predictor](https://pypi.org/project/madrigal-predictor/) version
0.1.1, whose own pinned dependencies are listed in
[consensus_model_package](https://github.com/staller-lab/consensus_model_package).

---

## Key files

### Final PARROT inputs, in `compressed_data`

| File | Contents |
|---|---|
| `parrot_input_all_six.tsv.gz` | Input for the final model (230,289 sequences) |
| `parrot_input_no_<predictor>.tsv.gz` | Inputs for the leave-one-out models |

---
