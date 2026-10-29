# CADNN: Consensus Activation Domain Neural Network

CADNN is a bidirectional LSTM (trained with PARROT) that takes a protein sequence of any length and predicts, for each residue, the fraction of six activation domain (AD) predictors that call that residue part of an AD. The six predictors are:

- PADDLE
- TADA
- ADpred
- ADhunterLite
- ADhunterEnsemble
- Kotha Composition Model

Work is split across two project directories on Savio:

```
SANJANA = /global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor
CLAIRE  = /global/scratch/projects/fc_mvslab/OpenProjects/Claire/consensus_predictor
```

---

## Pipeline overview

| Step | What happened | Sequences remaining |
|---|---|---|
| 1 | Collected sequences from Y1000+ yeast, PlantTFDB, and InterPro (DBD families), then de-duplicated | 583,621 |
| 2 | Length filter: 53 aa (PADDLE minimum) to 1,442 aa (99th percentile) | 576,616 |
| 3 | Disorder filter: at least 20% predicted disorder | 497,983 |
| 4 | Clustered with `mmseqs cluster` at 75% identity, kept one representative per cluster | 243,151 |
| 5 | Compiled test sets from published screens | — |
| 6 | Removed training sequences similar to test screen sequences | 232,797 |
| 7 | Removed training sequences similar to synthetic sequences | 230,302 |
| 8 | Split sequences into chunks of 1,000 | — |
| 9 | Ran all six predictors on the training and test sequences | — |
| 10 | Binarized predictions and combined them into per-residue consensus traces | — |
| 11 | Made an alternative input with folded domains masked to zero (metapredict2) | — |
| 12 | Removed PADDLE test-set TFs, then trained PARROT (the full model plus leave-one-out models) | 230,289 |
| 13 | Evaluated on full-length TFs and on screen tiles | — |

**Overlap filter used in steps 6 and 7:** a training sequence was removed if it covered more than 90% of a test or synthetic sequence at 30% or higher sequence identity (`mmseqs search`).

---

## Step details

### 1. Input sequences

- **Y1000+ yeast** (n = 172,854): homologs of *S. cerevisiae* TFs.
  - File: `SANJANA/output/cl_seqs.fasta`
- **PlantTFDB** (n = 310,656):
  - File: `SANJANA/PlantTFDB-all_TF_pep.fas`
- **InterPro** (n = 137,436):
  1. Took DBD families from Lambert et al. 2018, keeping families with more than one known human TF and dropping duplicates and the "unknown" category.
  2. Mapped each family to an InterPro domain or superfamily. The mapping is tracked in a Google Sheet.
  3. Pulled UniProt sequences with evidence levels 1 and 2.
  - File: `SANJANA/output/interpro_uniprot_evid_1_2.fasta`

### 5. Test sets

Test sets came from screens that were not used to train any of the individual predictors:

- **ARF** (Morffy et al.): Supplementary Table S3.
- **Sanborn**: sub-libraries D and E only. Sub-libraries A and B were used to train PADDLE.
- **Hummel**: `hummel_ratio_20230530`. This set was included in the overlap filter but was not used for final evaluation, because ADhunterEnsemble was trained on it.
- **Erkine / Ravarani**: supplementary tables of measured activities.
- **Arnold**: fold change ≥ 1.5 and P ≤ 1e-5, using tables EV2, EV4, EV5, and EV6.
- **DelRosso**: 25 randomly chosen TFs out of 1,241. We used a subset so that most human TFs stay in the training data.
- **Sog1**
- **Synthetics**

Activities for the test tiles are in `SANJANA/output/screen_test_seqs_with_activities.csv`.

> **Note on DelRosso:** a merge bug mapped about 1,200 tiles to the 25 DelRosso TFs instead of the correct ~800. All ~1,200 tiles were used when removing training sequences, which removed roughly 3,000 extra training sequences. We did not redo the clustering, because the predictions had already been run. The activities file above uses the correct 804 tiles.

### 9–10. Running predictors and building consensus

1. **Tiling:** each protein was tiled with a 1 aa step at each predictor's input length:
   - PADDLE and ADhunterEnsemble: 53 aa
   - TADA and ADhunterLite: 40 aa
   - ADpred: 30 aa
2. **Calling AD residues:** a residue counts as an AD residue for a given predictor if it falls in any tile that passes that predictor's published threshold.
3. **Consensus:** the consensus value for each residue is the fraction of predictors that call it.

### 11. Masked variant

Consensus traces were set to zero wherever they overlap a metapredict2 folded domain.

Across screens, the masked version performed worse than the unmasked consensus.

### 12. Training

- **Model:** PARROT bidirectional LSTM, regression task, one-hot encoded input.
- **Settings:** 1 hidden layer, hidden vector size 10, learning rate 0.001.
- **Data split:** random 70 / 15 / 15 train / validation / test.
- **Stopping:** training stopped after validation performance plateaued for 10 epochs.

Models trained:

- The all-six model.
- Leave-one-out models, each dropping one predictor.

Before training, we removed the 17 full-length TFs (*Saccharomyces* orthologs plus P07249) that are in the PADDLE test set.

### 13. Evaluation

- **Classification:** residue-level PRC and ROC on full-length TFs with known ADs.

  | Dataset | Full-length TFs |
  |---|---|
  | Yeast | 16 |
  | Fly | 49 |
  | Plant | 356 |
  | Human | 25 |

- **Regression:** Pearson and Spearman correlation against screen tile activities. When a tile was longer than a predictor's input, we scored the tile's sub-tiles and took the mean or the max.

---

## Notebooks

### In `SANJANA/notebooks/`

| Notebook | What it does |
|---|---|
| `00_Downloading all InterPro-superfamilies.ipynb` | Downloads UniProt sequences (evidence levels 1 and 2) for the InterPro codes matching the Lambert 2018 DBD families |
| `01_Input data clusters.ipynb` | Combines the three sources, de-duplicates, and applies the length and disorder filters |
| `02_Input data clusters with mimum sequence identity.ipynb` | Clusters sequences with mmseqs2 at 75% identity ("Running mmseqs2" section) |
| `03_Generating test set.ipynb` | Builds the test set from the published screens, then removes test-similar training sequences with mmseqs search ("Trying mmseqs search instead" section) |
| `04_Removing synthetics from training.ipynb` | Removes training sequences similar to the synthetic sequences |
| `05_Running predictors on train with test removed.ipynb` | Drops the Y1000+ (CL) sequences and splits the rest into chunks of 1,000 for prediction |
| `06_Binarized predictions to traces.ipynb` | Binarizes predictor outputs and converts them into per-residue consensus traces, producing the PARROT input |
| `07_Masking structured regions.ipynb` | Makes the folded-domain-masked version of the training input using metapredict2 |
| `Evaluation datasets.ipynb` | Plots predicted vs. measured activity for the consensus models and the individual predictors on each screen |
| `Eval consensus model.ipynb` | Counts TP and FP on human TFs (work in progress) |

### In `CLAIRE/`

| Notebook | What it does |
|---|---|
| `checking_seq_sets.ipynb` | Reconciles the predicted sequences with the final 230,302-sequence training set. It removes 2,492 sequences that were left over from before the synthetics filter, and it splits the remaining sequences into Y1000+ (CL) sequences (95,634) and non-CL sequences (134,655) |
| `loading_and_filtering_yeast_preds.ipynb` | Pulls the predictions for the filtered Y1000+ sequences |
| `make_parrot_input.ipynb` | Combines all predictions and writes the PARROT input files, one for the all-six model and one for each leave-one-out model |

---

## Bash scripts

### In `SANJANA/scripts/jobs/`

| Script | What it does |
|---|---|
| `run_CL_dask_all_split.sh` | Runs the predictors (parallelized with Dask) on the chunked training sequences |
| `run_CL_dask_all_split_on_missing.sh` | Re-runs the predictors on any chunks or tiles missing from the first run |
| `run_CL_dask_test_screen_seqs.sh` | Runs the predictors on the test screen sequences |
| `train_parrot.sh` | Trains the original PARROT consensus model |

### In `CLAIRE/`

| Script | What it does |
|---|---|
| `run_adhunter_ensemble_gpu.sh` | Runs ADhunterEnsemble on the GPU for each sequence chunk |
| `make_consensus.sh` | Combines the six predictors into consensus files for each chunk, for the all-six set and each leave-one-out set |
| `train_parrot_all_six.sh` | Trains the final CADNN model on all six predictors |
| `train_parrot_no_<predictor>.sh` | Trains the leave-one-out models. Variants: `no_composition`, `no_ADhunterEnsemble`, `no_ADhunterLite`, `no_tada`, `no_paddle`, `no_adpred` |

To merge the per-chunk consensus files, run the following from `CLAIRE/predictions/combined_preds`, once for each variant:

```bash
head -n 1 pt1_combined_all_six.csv > non_cl_seqs_all_six_combined.csv
tail -q -n +2 pt*_combined_all_six.csv >> non_cl_seqs_all_six_combined.csv
```

---

## Key files

### Training data, in `SANJANA/`

| File | Contents |
|---|---|
| `data/CL_SK_plant_input.fasta` | Sequences after the length filter |
| `data/CL_SK_plant_seqs_disord_thresh.fasta` | Sequences after the disorder filter |
| `output/mmseqs/CL_SK_plant_seqs_disord_thresh_DB_clu_id75.tsv` | mmseqs2 clusters |
| `data/train_seqs_with_test_overlap_removed.fasta` | Training sequences with test-similar sequences removed |
| `data/train_seqs_with_test_synthetics_overlap_removed.fasta` | Final training sequences (230,302) |
| `data/non_cl_train_seqs_split/pt*.fasta` | Training sequence chunks used for prediction |

### Predictions and PARROT input, in `SANJANA/`

| File | Contents |
|---|---|
| `output/train_seqs_with_test_overlap_removed_sk_only/` | Predictions on the training sequences |
| `output/screen_test_seqs_preds/` | Predictions on the test screen sequences |
| `output/parrot_input_test_synthetics_removed.tsv` | Original PARROT input (without ADhunterEnsemble) |

### Final PARROT inputs, in `CLAIRE/predictions/combined_preds/final_data/`

| File | Contents |
|---|---|
| `parrot_input_all_six.tsv` | Input for the final model (230,289 sequences) |
| `parrot_input_no_<predictor>.tsv` | Inputs for the leave-one-out models |

---

## Known loose ends

- **Missing sequences:** the final inputs have 230,289 sequences, 13 fewer than the 230,302 in the training set. The missing names are listed in `CLAIRE/missing_seqs.txt`.
- **DelRosso over-removal:** the training set is missing about 3,000 extra sequences because of the DelRosso tile bug described in step 5.
