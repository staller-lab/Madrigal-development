00_Downloading_all_InterPro-superfamilies.ipynb: Gets seqences from uniprot with TF DBDs. Used Lambert 2018 paper’s list of DBD families. Writes sequences to data/interpro_seq_uniprotids.csv and to data/interpro_uniprot_evid_1_2.fasta. 

01_Input_data_clusers.ipynb: Loads both uniprot sequences and y1000+ sequences. We used all y1000+ orthogroups that contained at least one S. cerevisiae DBD. 