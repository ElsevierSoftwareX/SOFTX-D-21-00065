import pandas as pd
import numpy as np
import shutil
from . import get_rootdir
import os
from .country2ISO import country2ISO

def indicators2key(df_key, prefix=''):
    '''
    Concatenate the values in df_key to create a key
    
    Parameters
    ----------
    df_key : pandas dataframe
        dataframe where each column is a component of a key
    prefix : str
        prefix to be used at the beginning of the key (typically the countryname)
    
    Returns
    -------
    list
        List of the created keys
    '''
    #we cannot substitute -1 with na as some will be used as indexes!
    df_key.fillna(-1, inplace=True)
    
    df_key = df_key.values.astype(int).astype(str)
    if prefix == '':
        key = ['_'.join(x) for x in df_key]
    else:
        key = [f'{prefix}_' + '_'.join(x) for x in df_key]
        
    return(key)

def sample_by_column(df, column, N=1, seed=1234):
    '''
    Sample N rows for each unique value in a column.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe from which to sample the rows
    column : str
        Column use to obtain the group the rows and sample one row for each
        unique value.
    N : int
        Number or rows sampled
    seed : int
        Seed to initialize the pseudo-random number generator

    Returns
    -------
    pandas.Dataframe
        Dataframe with the sampled rows

    '''
    np.random.seed(seed)
    
    #sample one row for each value
    df_sampled = df.groupby(column, group_keys=False).apply(lambda df: df.sample(N))
    return(df_sampled)

def select_age(df, age_col, age_low, age_high):
    df_age = df.query(f'{age_col} >= @age_low & {age_col} <= @age_high')
    return(df_age)

def recode_nans(df, column, nans = []):
    '''
    Sample N rows for each unique value in a column.

    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe to process
    column : str
        Traget column
    nans : list
        List of values to be recoded as nans
    
    Returns
    -------
    pandas.Dataframe
        Dataframe with the recoded values

    '''
    recode_dict = {}
    for value in nans:
        recode_dict[value] = np.nan
    df[column].replace(recode_dict, inplace=True)
    return(df)

def get_rows_all_nan(df):
    '''
    Obtain the (numerical) indices of rows in the df that contain all nans
    
    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe to query
        
    Returns
    -------
    numpy.array :
        (Numerical) indices of rows with all nans
    '''
    sum_nans = (df.isna()==True).sum(axis=1)
    idx_all_nan = np.where(sum_nans == df.shape[1])[0]
    return(idx_all_nan)
    
def remove_rows_all_nan(df, return_indexes = False):
    '''
    Remove rows in the df that contain all nans
    
    Parameters
    ----------
    df : pandas.DataFrame
        Dataframe to process
    return_indices : bool
        True return the (numerical) indices of the rows that have been removed
        
    Returns
    -------
    pandas.DataFrame
        Processed dataframe
    numpy.array :
        (Numerical) indices of rows with all nans (if return_indices=True)
    '''
    idx_all_nan = get_rows_all_nan(df)
    idx_to_keep = np.delete(np.arange(df.shape[0]), idx_all_nan)
    df = df.iloc[idx_to_keep, :]
    if return_indexes:
        return(df, idx_to_keep)
    else:
        return(df)

def get_countryname(micsround, country, get_ISO = False):
    '''
    Obtain the country name from the name of a folder in a MICS dataset
    
    Parameters
    ----------
    micsround : int
        Round of the MICS
    country : str
        Name of the folder
    get_ISO : boolean, optional
        Whether to return the ISO code of the country instead of the name, 
        according to the country2ISO dictionary in the mics_library
        
    Results
    -------
    str : 
        Name of the country (or ISO code if get_ISO = True)
    '''
    #TODO use ISO instead of country names
    
    if micsround in [3, 5]:
        countryname = country.split(' MICS')[0]
    elif micsround == 4:
        countryname = country.split('_MICS4_')[0]
    else:
        countryname = country
    
    if get_ISO:
        ISO = country2ISO[countryname]
        return(ISO)
    else:
        return(countryname)

def drop_duplicated_indices(dataframe, how='first', dupl_indices=None):
    
    def _mymode(x):
        if x.isna().sum() == len(x):
            return(np.nan)
        else:
            return(x.value_counts().index[0])
            
    return_indices = False
    
    if dupl_indices is None:
        return_indices = True
        dupl_indices = dataframe.index[np.where(dataframe.index.duplicated())[0]]
        
    dataframe_dupl = dataframe.loc[dupl_indices]
    dataframe_nodupl = dataframe.drop(dupl_indices, axis=0)
    
    if how == 'mean':
        dataframe_dupl = dataframe_dupl.groupby(dataframe_dupl.index).mean()
    elif how == 'mode':
        dataframe_dupl = dataframe_dupl.groupby(dataframe_dupl.index).agg(lambda x: _mymode(x))
    elif how == 'first':
        dataframe_dupl = dataframe_dupl[~dataframe_dupl.index.duplicated(keep='first')]
    elif how == 'last':
        dataframe_dupl = dataframe_dupl[~dataframe_dupl.index.duplicated(keep='last')]
    
    dataframe = pd.concat([dataframe_dupl, dataframe_nodupl], axis=0)
    
    if return_indices:
        return(dataframe, dupl_indices)
    else:
        return(dataframe)

def unfold_MICS4():
    '''
    MICS 4 data downloaded from UNICEF are organized as follows:
        [COUNTRY_FOLDER]
           Readme_xxxx
           [SUBFOLDER_COUNTRY]
               ...questionnaires files
    
    This function copies the questionnaire files in the main COUNTRY_FOLDER
    and removes the SUBFOLDER_COUNTRY.
    
    Guinea Bissau should be manually removed as the datafiles are not in the correct format
    '''
    
    MICS_ROOTDIR = get_rootdir()
    DATADIR = os.path.join(MICS_ROOTDIR, 'MICS4')
    
    countries = os.listdir(DATADIR)
    
    #%
    for country in countries:
        COUNTRY_FOLDER = os.path.join(DATADIR, country)
        items_country = os.listdir(COUNTRY_FOLDER)
        
        for item in items_country:
            
            # if it is folder
            if os.path.isdir(os.path.join(COUNTRY_FOLDER, item)):
                
                # copy all files in the country folder
                files_in_folder = os.listdir(os.path.join(COUNTRY_FOLDER, item))
                
                for file in files_in_folder:
                    shutil.copyfile(os.path.join(COUNTRY_FOLDER, item, file),
                                    os.path.join(COUNTRY_FOLDER, file))
                
                # remove folder
                shutil.rmtree(os.path.join(COUNTRY_FOLDER, item))