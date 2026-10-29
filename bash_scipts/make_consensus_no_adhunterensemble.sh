#!/bin/bash
# Job name:
#SBATCH --job-name=consensus
#
# Account:
#SBATCH --account=fc_mvslab
#
# Partition:
#SBATCH --partition=savio3
#
# Number of nodes:
#SBATCH --nodes=1
#
# Number of tasks
#SBATCH --ntasks=1
#
# Processors per task:
#SBATCH --cpus-per-task=32
#
# Wall clock limit:
#SBATCH --time=36:00:00
#
#SBATCH --output=../logs/consensus_no_adhunterensemble_%A_%a.out
#SBATCH --array=1-138
#
## Command(s) to run:

source activate /global/scratch/users/claireleblanc/conda_environments/dask_v3

echo "Starting preds"
python "../other_scripts/generate_consesnus_prediction_v2.py" -p "pt${SLURM_ARRAY_TASK_ID}" -d "../predictions" -o "combined_preds/pt${SLURM_ARRAY_TASK_ID}_combined_no_ADhunterEnsemble.csv" -ah -ap -t -pa -c
