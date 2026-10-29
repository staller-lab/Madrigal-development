#!/bin/bash
#SBATCH --job-name=dask_all_preds_split_input
#SBATCH --account=ac_stallerlab
#SBATCH --partition=savio2_bigmem
#
# Number of nodes:
#SBATCH --nodes=1
#
# Number of tasks (array size, adjust as needed):
#SBATCH --ntasks=1
#SBATCH --array=143
#
# Processors per task:
#SBATCH --cpus-per-task=24
#SBATCH --mem=120G
#
# Wall clock limit:
#SBATCH --time=1:30:00
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
INPUT_FILE="/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/data/non_cl_train_seqs_split/adhunter_tada_missing_preds_pt${SLURM_ARRAY_TASK_ID}.fasta"
OUTPUT_DIR="/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/output/train_seqs_with_test_overlap_removed_sk_only"

# Run the Python script with the correct input file for each task in the array
srun /global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/conda/new_dask/bin/python \
    "/global/scratch/projects/fc_mvslab/predictors/all_predictors/running_all_in_parallel_w_dask/run_all_dask.py" \
    -f "$INPUT_FILE" \
    -o "$OUTPUT_DIR" -np -nad