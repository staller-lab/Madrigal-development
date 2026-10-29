#!/bin/bash
#SBATCH --job-name=dask_all_preds_screen_seqs
#SBATCH --account=ac_stallerlab
#SBATCH --partition=savio2_bigmem
#
# Number of nodes:
#SBATCH --nodes=1
#
#
# Processors per task:
#SBATCH --cpus-per-task=24
#SBATCH --mem=120G
#
# Wall clock limit:
#SBATCH --time=72:00:00
#
#SBATCH --export=ALL
#SBATCH --mail-type=ALL
#SBATCH --mail-user=sanjana.kotha@berkeley.edu
#SBATCH --output=../logs/CL_dask_all_preds_%A_%a.log  
## Command(s) to run:

unset SLURM_MEM_PER_CPU
unset SLURM_MEM_PER_GPU
unset SLURM_MEM_PER_NODE

export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

export TF_NUM_INTRAOP_THREADS=1
export TF_NUM_INTEROP_THREADS=1

# Activate the conda environment
source activate /global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/conda/new_dask

# Define the input file based on the task array index
INPUT_FILE="/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/data/long_test_seqs_duplicates_dropped.fasta"
OUTPUT_DIR="/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/output/screen_test_seqs_preds"

# Run the Python script with the correct input file for each task in the array
srun /global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/conda/new_dask/bin/python \
    "/global/scratch/projects/fc_mvslab/predictors/all_predictors/running_all_in_parallel_w_dask/run_all_dask.py" \
    -f "$INPUT_FILE" \
    -o "$OUTPUT_DIR"