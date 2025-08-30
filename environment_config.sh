#Configuration file for web application

R packages:
install.packages("BiocManager")
BiocManager::install("DESeq2")
#Need Libraries:
dash
plotly
pandas
scikit-learn
rpy2
matplotlib

General workflow:

1. wget and install conda
2. Check for R and install if not present
3. Create a new conda environment
'conda create -n r_env -c conda-forge python=3.10 r-base rpy2 libstdcxx-ng
'
4. Install the required libraries
'conda activate r_env
conda install -c conda-forge dash plotly pandas scikit-learn matplotlib
'
5. create .yaml file to pip install python libraries in new conda environment