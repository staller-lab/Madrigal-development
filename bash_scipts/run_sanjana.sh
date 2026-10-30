#!/bin/bash
# Job name:
#SBATCH --job-name=dask
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
#SBATCH --output=logs/composition_%A_%a.out
#
#SBATCH --array=2-138
#
# Wall clock limit:
#SBATCH --time=36:00:00
#
## Command(s) to run:

# module load openjdk/17.0.8.1_1-gcc-11.4.0

export OMP_NUM_THREADS=1
export TF_NUM_INTRAOP_THREADS=1
export TF_NUM_INTEROP_THREADS=1

FILE1="../predictions/pt${SLURM_ARRAY_TASK_ID}_orthologs_s_001_lcc_VP16_lch_006_ucc_-08_uch_CITED2_lcs1_inf_lcs2_000_lcs1_inf_ucs2_inf_comp_WFL_tl_039_ws_001_ps1_Charge_ps2_AllHydros"
if [ ! -f $FILE1 ]; then
	srun python /global/scratch/users/claireleblanc/scripts/run_sanjana.py -f "/global/scratch/projects/fc_mvslab/OpenProjects/Sanjana/consensus_AD_predictor/data/non_cl_train_seqs_split/pt${SLURM_ARRAY_TASK_ID}.fasta" -o "/global/scratch/projects/fc_mvslab/OpenProjects/Claire/consensus_predictor/predictions/"
else
	echo "${SLURM_ARRAY_TASK_ID} already has Sanjana predictions"
fi

