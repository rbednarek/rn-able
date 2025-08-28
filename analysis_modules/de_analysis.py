from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def plot_count_pca(count_df, 
                   raw_count=10, 
                   min_samples=3, 
                   components=2, 
                   log=True, 
                   plot=True,
                   meta_df=None,
                   col1=None,
                   col2=None,
                   exp=None):
    pca = PCA(n_components=components)
    count_filter = count_df.loc[:, (count_df > raw_count).sum(axis=0) >= min_samples]
    if log:
        count_filter = np.log1p(count_filter)
    pca_result = pca.fit_transform(count_filter.T)
    variance = pca.explained_variance_ratio_ *100
    pc1_variance = round(variance[0], 2)
    pc2_variance = round(variance[1], 2)

    pca_df = pd.DataFrame(pca_result, columns=['PC1', 'PC2'], index=count_filter.columns)
    if meta_df is not None:
        pca_df = pca_df.join(meta_df, how='left')
    if plot:
        plt.figure(figsize=(8, 6))
        if meta_df is not None:
            markers = ['o', 's', '^', 'D', 'X', 'P', '*']
            if col2 and col2 in pca_df.columns:
                for (color, shape), group in pca_df.groupby([col1, col2]):
                    plt.scatter(group['PC1'], group['PC2'], label=f'{color}-{shape}', marker=markers[hash(shape) % len(markers)])
            elif col1 and col1 in pca_df.columns:
                for color, group in pca_df.groupby(col1):
                    plt.scatter(group['PC1'], group['PC2'], label=color)
        else:
            plt.scatter(pca_df['PC1'], pca_df['PC2'])
        if exp:
            plt.title(f'{exp} - Count Data PCA')
        else:
            plt.title('Count Data PCA')    
        plt.xlabel(f'PC1 ({pc1_variance}%)')
        plt.ylabel(f'PC2 ({pc2_variance}%)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid()
        plt.show()
    return pca_df, pc1_variance, pc2_variance

