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
#SBATCH --output=logs/predict_parrot_%A_%a.log

export MPLBACKEND=Agg

INPUT_TSV="../test_seq_predictions/synthetics_test_seqs.tsv"
OUTPUT_PT="../models/consensus_model_no_tada.pt"
OUTPUT_FILE="../test_seq_predictions/synthetics_preds_no_tada_model.csv"

echo "Activating conda environment..."
source activate /global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/conda/parrot_fixed

echo "Running command:"
echo "parrot-optimize \"$INPUT_TSV\" \"$OUTPUT_PT\" \"$OUTPUT_FILE\" -d residues -c 1"

parrot-predict "$INPUT_TSV" "$OUTPUT_PT" "$OUTPUT_FILE" -d residues -c 1

echo ""
