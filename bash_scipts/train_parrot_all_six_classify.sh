#!/bin/bash
#SBATCH --job-name=train_parrot
#SBATCH --account=fc_mvslab
# Partition:
#SBATCH --partition=savio3_gpu
#
# GPU settings:
#SBATCH --gres=gpu:GTX2080TI:1
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
# For some reason this node isn't working for gpu
#SBATCH --exclude=n0158.savio3
#
#SBATCH --time=12:00:00
#SBATCH --output=logs/train_parrot_%A_%a.log

export MPLBACKEND=Agg

INPUT_TSV="predictions/combined_preds/final_data/parrot_input_all_six_classify.tsv"
OUTPUT_PT="models/consensus_model_all_six_classify.pt"

echo "Activating python environment..."
source /global/scratch/users/claireleblanc/conda_environments/conda_environments/parrot_v2/bin/activate

echo "Running command:"
echo "parrot-train \"$INPUT_TSV\" \"$OUTPUT_PT\" -d residues -c 1 --epochs 10 --stop 'auto'"

parrot-train "$INPUT_TSV" "$OUTPUT_PT" -d residues -c 7 --epochs 10 --stop 'auto' --save-splits

echo ""
