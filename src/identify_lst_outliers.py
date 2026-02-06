import pandas as pd
import numpy as np
from pathlib import Path

def linear_reg(X,y):
    X_mat = X.values
    y_mat = y.values

    # Formula: inv(X.T @ X) @ X.T @ y
    # @ is the symbol for matrix multiplication in Python
    xtx = X_mat.T @ X_mat
    xtx_inv = np.linalg.inv(xtx)
    xty = X_mat.T @ y_mat

    coeffs = xtx_inv @ xty
    coeffs = pd.Series(coeffs, index=X.columns)
    return coeffs

def identify_lst_outliers_linreg(dfls):
    tmpdf = dfls.copy()

    # encode sold date
    sdate = tmpdf['sold_date'].min()
    edate = tmpdf['sold_date'].max()
    dr = pd.Series(pd.date_range(start=sdate, end=edate, freq='D').sort_values(ascending=True))
    dr_idx_map = pd.Series(dr.index, index=dr.values)
    tmpdf['_n'] = tmpdf['sold_date'].map(dr_idx_map)

    # run regression
    tmpdf['intercept'] = 1
    X = tmpdf[['intercept','_n']]
    y = tmpdf['price']
    coeffs = linear_reg(X,y)
    tmpdf['yhat'] = X @ coeffs
    tmpdf['residuals'] = tmpdf['price'] - tmpdf['yhat']
    return dfls

def identify_lst_outliers(dfls):
    tmpdf = dfls.copy()
    if 'include_lst_filters' in tmpdf.columns:
        idx = tmpdf.loc[tmpdf['include_lst_filters']].index
    else:
        idx = tmpdf.index

    # mad
    median = tmpdf.loc[idx, 'price'].median()
    mad = (tmpdf.loc[idx, 'price'] - median).abs().median()
    std_robust = mad * 1.4826

    # get thresholds
    width = 5
    upper_thr = max(median + width*std_robust, 0)
    lower_thr = median - width*std_robust

    # identify outliers
    tmpdf['is_outlier'] = False
    mask = (tmpdf['price']>upper_thr) | (tmpdf['price']<lower_thr)
    mask = mask & (tmpdf.index.isin(idx))
    dfls['is_outlier'] = mask
    return dfls


if __name__ == '__main__':
    dfls = pd.read_pickle(f'{Path.cwd().parent}/saved_data/dfls.pkl')
    dfls = identify_lst_outliers(dfls)
    pass