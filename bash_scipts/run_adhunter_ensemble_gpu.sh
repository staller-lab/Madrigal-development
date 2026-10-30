#!/bin/bash
# Job name:
#SBATCH --job-name=adhunter_ensemble
#
# Account:
#SBATCH --account=fc_mvslab
#
# Partition:
#SBATCH --partition=savio3_gpu
#
# GPU settings:
#SBATCH --gres=gpu:GTX2080TI
#SBATCH --qos=gtx2080_gpu3_normal
#
# Number of nodes:
#SBATCH --nodes=1
#
# Number of tasks
#SBATCH --ntasks=1
#
# Processors per task:
#SBATCH --cpus-per-task=2
#
# Wall clock limit:
#SBATCH --time=24:00:00
#
#SBATCH --output=logs/adhunter_esm_%A_%a.out
#SBATCH --array=2
#
# For some reason this node isn't working for gpu
#SBATCH --exclude=n0158.savio3
#
## Command(s) to run:

module load gcc
module load cuda/11.8.0 #11.8 for environment compatibility
module load anaconda3

echo "Start: $(date +%T)"
echo "SLURM_ARRAY_TASK_ID: $SLURM_ARRAY_TASK_ID"
echo "HOSTNAME: $HOSTNAME"
echo "SLURM_NODELIST: $SLURM_NODELIST"
nvidia-smi

FILE1=$(printf "/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/data/non_cl_train_seqs_split/pt%d.fasta" $SLURM_ARRAY_TASK_ID)

export TORCH_HOME=/global/scratch/projects/fc_mvslab/predictors/ADhunter_ensemble/.cache/torch
FILE2="../predictions/pt${SLURM_ARRAY_TASK_ID}_ADhunter_ensemble_preds.csv"

if ([ ! -f $FILE2 ]); then
	conda run --no-capture-output -p /global/scratch/users/claireleblanc/conda_environments/adhunter_esm python /global/scratch/projects/fc_mvslab/predictors/ADhunter_ensemble/03-run/run_ESM_and_ADhunter.py -f $FILE1 -o predictions  --use-gpu
else
	echo "${SLURM_ARRAY_TASK_ID}" already has predictions
fi

echo "End: $(date +%T)"

