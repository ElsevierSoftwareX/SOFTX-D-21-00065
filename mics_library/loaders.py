import numpy as np
import pandas as pd
import pyreadstat
from .utils import get_countryname, indicators2key, drop_duplicated_indices
from .swap_indicators import merge_swap_indicators
from . import get_rootdir
import os

def _get_key_cols(questionnaire, micsround):
    '''
    Define the keys that are computed for each questionnaire,
    with the indicators that compose each key
    and the swap_indicators dictionary to correct inconsistencies with the 
    indicator names
    
    Parameters
    ----------
    questionnaire : str
        The questionaire for which to compute the keys.
        'hh', 'hl', 'ch', 'wm', 'mn', 'bh' are valid questionnaires
    micsround : int
        The round of the mics
    
    Returns
    -------
    dict
        {name_of_key: [list of indicators composing the key]}
    
    dict
        a swap indicator dict for the questionnaire
    '''
    assert micsround in [3, 4, 5], "only implemented for mics 3, 4, 5"

    keys_dict = {'HHID': ['HH1', 'HH2']}
    
    if questionnaire == 'hl':
        if micsround == 3:
            keys_dict['HLID'] = ['HH1', 'HH2', 'HL1']
            keys_dict['mother_HLID'] = ['HH1', 'HH2', 'HL10']
            keys_dict['father_HLID'] = ['HH1', 'HH2', 'HL12']

        elif micsround == 4:
            #!!! There are HL8 and HL9 too: use them?
            keys_dict['HLID'] = ['HH1', 'HH2', 'HL1']
            keys_dict['mother_HLID'] = ['HH1', 'HH2', 'HL12']
            keys_dict['father_HLID'] = ['HH1', 'HH2', 'HL14']
        
        elif micsround == 5:
            keys_dict['HLID'] = ['HH1', 'HH2', 'HL1']
            keys_dict['mother_HLID'] = ['HH1', 'HH2', 'HL12']
            keys_dict['father_HLID'] = ['HH1', 'HH2', 'HL14']
            
    elif questionnaire == 'wm':
        if micsround == 3:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']
            
        elif micsround == 4:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']
            
        elif micsround == 5:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']
            
    elif questionnaire == 'mn':
        if micsround == 4:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']
            
        elif micsround == 5:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']
            
    elif questionnaire == 'ch':
        if micsround == 3:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']#,
            keys_dict['caretaker_HLID'] =  ['HH1', 'HH2', 'UF6']
            
        elif micsround == 4:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']#,
            keys_dict['caretaker_HLID'] =  ['HH1', 'HH2', 'UF6']
            
        elif micsround == 5:
            keys_dict['HLID'] = ['HH1', 'HH2', 'LN']#,
            keys_dict['caretaker_HLID'] =  ['HH1', 'HH2', 'UF6']
    
    elif questionnaire == 'bh':
        if micsround == 4:
            keys_dict['HLID'] = ['HH1', 'HH2', 'BH8']#,
            keys_dict['mother_HLID'] =  ['HH1', 'HH2', 'LN']
            
        elif micsround == 5:
            keys_dict['HLID'] = ['HH1', 'HH2', 'BH8']#,
            keys_dict['mother_HLID'] =  ['HH1', 'HH2', 'LN']
            
    elif questionnaire == 'hh':
        if micsround == 3:
            keys_dict['child_HLID'] = ['HH1', 'HH2', 'CD11']
        
        elif micsround == 4:
            keys_dict['child_HLID'] = ['HH1', 'HH2', 'CD9']
            
        elif micsround == 5:
            keys_dict['child_HLID'] = ['HH1', 'HH2', 'SL9B'] #TODO: CHECK
            
    return(keys_dict)

def _compute_keys(questionnaire, df, micsround, prefix = ''):
    '''
    Compute the keys of a datframe, given the questionnaire, micsround and country
    
    Parameters
    ----------
    questionnaire : str
        The questionaire for which to compute the keys.
        'hh', 'hl', 'ch', 'wm', 'mn', 'bh' are valid questionnaires
    df : pandas.Dataframe
        The dataframe for which to compute the keys
    micsround : int
        The round of the mics
    prefix : string
        Prefix to be used at the beginning of the key;
        typically: MICSROUND_COUNTRY
    
    Returns
    -------
    dict
        {df_key: key_values}
    
    '''
    #TODO: check if we can avoid to require micsround and country
    #e.g. pre-pending the prefix after this function has been called
    key_cols_quest = _get_key_cols(questionnaire, micsround)
    
    keys = {}
    for key_name in key_cols_quest.keys():
        columns_key = key_cols_quest[key_name]
        df_keys = df.reindex(columns = columns_key)

        keys[key_name] = indicators2key(df_keys, prefix)
    
    if questionnaire == 'hh':
        keys['index'] = keys['HHID']
    elif questionnaire == 'hl':
        keys['index'] = keys['HLID']
    elif questionnaire == 'wm':
        keys['index'] = keys['HLID']
    elif questionnaire == 'mn':
        keys['index'] = keys['HLID']
    elif questionnaire == 'ch':
        keys['index'] = keys['HLID']
    elif questionnaire == 'bh':
        keys['index'] = keys['HLID']
   
    return(keys)

def load_sav(datafile, indicators, swap_indicators = {}, ignorecase=True):
    '''
    Load a .sav file containing MICS data (as downloaded from UNICEF).
    Load only the selected indicators, 
    managing the indicators that should be swapped.
    
    Parameters
    ----------
    datafile : str
        Path to the .sav datafile from which to load the indicatora
    
    indicators : list of str
        Acronyms of the indicators to be loaded
    
    swap_indicators : dict
        {country : { correct_acronym : acronym_in_country },
         ...
        }
        Used to deal with different acronym names between countries.
        For each country, 
        load acronym_in_country instead of correct_acronym
        and rename it as correct_acronym
    
    ignorecase : bool, optional
        Whether to ignore cases of characters of acronyms. Default True
    
    Returns
    -------
    pandas.DataFrame : df
        Dataframe with the loaded data
    pandas.DataFrame : meta
        Dataframe with the metadata
    '''
    
    #manage swap indicators - BEFORE
    #add wrong indicators to the list of columns to load
    for k,v in swap_indicators.items():
        if k in indicators:
            indicators.append(v)
            indicators.remove(k)
    
    #manage upper-lowercase indicators
    if ignorecase:
        indicators_upper = [x.upper() for x in indicators]
        indicators_lower = [x.lower() for x in indicators]

        indicators = indicators_upper + indicators_lower
    
    df, meta = pyreadstat.read_sav(datafile, usecols = indicators)
    
    #manage swap indicators - AFTER
    #assign the correct names to the columns
    swap_indicators_inv = {v: k for k, v in swap_indicators.items()} #get inverse dict
    df.rename(swap_indicators_inv, axis='columns', inplace=True) #rename columns
    
    #all indicators to uppercase
    if ignorecase:
        df.columns = [x.upper() for x in df.columns]
        #CHECK: should I process meta too?
        #so far it is used only in get_dict and ignore_case is managed there
    
    return(df, meta)

def get_dict(meta, ignorecase=False):
    '''
    Obtain information about the label and values stored in a .sav file
    
    Parameters
    ----------
    meta : pandas.DataFrame
        Dataframe with metadata, obtained from mics_library.utils.load_sav
    ignorecase : bool
        True to ignore the cases of characters in the acronyms
        
    Returns
    -------
    dict
        Dictionary with the information:
        {acronym : {'label' : Description of the acronym,
                    'values' : { numerical_value : category }
                               If the acronym has categorical answers.
                    }
         }
    
    '''
    labels_dict = dict([(x,y) for x,y in zip(meta.column_names, meta.column_labels)])
    
    df_dict = {}
    for variable in labels_dict.keys():
        variable_dict={}
        variable_dict['label'] = labels_dict[variable]
        
        if variable in meta.variable_to_label:
            values = {}
            int2value_dict = meta.value_labels[meta.variable_to_label[variable]]
            for I in int2value_dict.keys():
                values[I] = int2value_dict[I]
            variable_dict['values'] = values
        if ignorecase:
            df_dict[variable.upper()] = variable_dict
        else:   
            df_dict[variable] = variable_dict
    return(df_dict)

def import_dataset(micsround, indicators, recoding_dictionary={}, swap_indicators = {}, ignorecase=True):
    '''
    Parameters
    ----------
    miscround : int
        The round of the mics
    indicators : dict
        Dictionary of questionnaires and their indicators to be checked.
        The required format is:
            key: questionnaire
            value: list of indicators
            e.g.:  {'hh': ['HH1', 'HH2'], 
                    'hl': [HL10, HL12]}
    recoding_dictionary : dict
        { questionnaire : { country : { indicator : recoding, ...}}}
        Dictionary used to define how some indicator values should be recoded 
        (based on recoding, a dictionary) to obtain consistent information.
        Typically a recoding_dictionary is automatically created based on a
        properly created csv file, using the 
        ```mics_library.utils.create_encoding_indicator(csvfile)```
        function.
    swap_indicators : dict
        { questionnaire : { country : { new_name_indic1 : name_indic1, ...}}}
        Dictionary used to define how some indicator names of some countries
        should be changed to comply with the names used in the majority of the
        countries.
    ignorecase: boolean, optional
        Whether to consider uppercase and lowercase acronyms the same. 
        Default True
    
    Returns
    -------
    dictionary
        Dictionary like {'questionnaire': {'country': [data, keys], ...}
        where data is a pandas' dataframe with the value of the indicators
        and keys is a pandas' dataframe with the keys
        for each country.
    '''
    
    MICS_ROOTDIR = get_rootdir()
    DATADIR = f'{MICS_ROOTDIR}/MICS{micsround}'
    countries = os.listdir(DATADIR)
    
    questionnaires = list(indicators.keys())
    
    #join custom and default swap_indicators
    swap_indicators = merge_swap_indicators(micsround, swap_indicators)
    
    #PROCESS ALL QUESTIONNAIRES
    data_all = {}
    for questionnaire in questionnaires:
        # print(questionnaire)
        
        #get indicators of the questionnaire to process
        indicators_questionnaire = indicators[questionnaire]
        
        #get recoding dict for this questionnaire
        recoding_dict_questionnaire = recoding_dictionary[questionnaire] if questionnaire in recoding_dictionary else {}
        
        #get swap indicators for this questionnaire
        swap_indicators_questionnaire = swap_indicators[questionnaire] if questionnaire in swap_indicators else {}
        
        #get additional columns needed to compute keys, and their swap dictionary
        key_cols_questionnaire = _get_key_cols(questionnaire, micsround)
        
        keys_columns = []
        for k,v in key_cols_questionnaire.items():
            keys_columns += v
        keys_columns = list(np.unique(keys_columns)) #additional needed columns
        
        #PROCESS ALL COUNTRIES
        data_questionnaire = {}
        for country in countries:
            countryname = get_countryname(micsround, country)
            # print(countryname)
            
            #get datafile
            datafile = os.path.join(MICS_ROOTDIR, f'MICS{micsround}', country, f'{questionnaire}.sav')
            
            if not os.path.exists(datafile): #file not found
                print(f'>>>>>>>>>>>>>>>>>> {datafile}  NOT FOUND')
            else:
                #get swap_indicators of this country
                swap_indicators_country = swap_indicators_questionnaire[countryname] if countryname in swap_indicators_questionnaire else {}
                
                #columns to be loaded are the selected + needed for the keys
                cols_to_be_loaded = indicators_questionnaire + keys_columns
                
                #load selected columns
                df, _ = load_sav(datafile, cols_to_be_loaded, swap_indicators_country, ignorecase)
                
                #recode values
                for indicator, indicator_dict in recoding_dict_questionnaire.items():
                    if (indicator in df.columns) and (countryname in indicator_dict):
                        indicator_dict_country = indicator_dict[countryname]
                        df[indicator].replace(indicator_dict_country, inplace=True)
    
                #compute keys                    
                keys = _compute_keys(questionnaire, df, micsround, f'{micsround}_{countryname}')
                
                #add index to df
                df.index = keys['index']
                
                #create dataframe with computed keys
                keys = pd.DataFrame(keys)
                keys.index = keys.pop('index')
                                
                #remove columns used to compute keys but not selected
                col_to_remove = []
                for c in keys_columns:
                    if (c not in indicators_questionnaire) and (c in df.columns):
                        col_to_remove.append(c)
                
                df.drop(col_to_remove, axis=1, inplace=True)
                
                # add country information to keys
                keys['country'] = np.repeat(countryname, df.shape[0])
    
                #add dataframe to the questionnaire dict
                data_questionnaire[countryname] = [df, keys]
                
            #CONTINUE WITH NEXT COUNTRY
        
        data_all[questionnaire] = data_questionnaire
        
        #CONTINUE WITH NEXT QUESTIONNAIRE
        
    return(data_all)

def merge_questionnaires(dataset, drop_na_index = True):
    '''
    Merge dataframe of multiple countries and multiple questionnaires 
    into a unique pandas.DataFrame. All merge operations are attempted with an
    'outer' join (see pandas.merge for more information).
    
    Parameters
    ----------
    dataset : dict
        The result of the mics_library.loaders.import_dataset function
    drop_na_index : bool (default True)
        Whether to drop rows that result with a nan as index value after a
        join operation between 'hh' and another questionnaire.
    
    Returns
    -------
    pandas.Dataframe
        The dataframe containing the merged data
    '''
    
    #TODO: issues with duplicated columns, try to use merge_questionnaires_manual
    
    # if only one questionnaire, just concat countries
    if len(dataset.keys()) == 1:
        quest = list(dataset.keys())[0]
        data = pd.concat([v[0] for k,v in dataset[quest].items()], axis=0)
        keys = pd.concat([v[1] for k,v in dataset[quest].items()], axis=0)
        return(data, keys)
    
    # if more than one questionnaire:
    
    #concatenate countries, by questionnaire
    data_all = {}
    keys_all = {}
    for quest in dataset.keys():
        #merge all countries
        data_quest = pd.concat([v[0] for k,v in dataset[quest].items()], axis=0)
        keys_quest = pd.concat([v[1] for k,v in dataset[quest].items()], axis=0)
        
        data_quest, dupl_indices = drop_duplicated_indices(data_quest, 'mode')
        keys_quest = drop_duplicated_indices(keys_quest, 'mode', dupl_indices)
        data_all[quest] = data_quest
        keys_all[quest] = keys_quest
    
    #if the hh questionaire is present,
    #we need to perform a separate merge, based on HHID
    if 'hh' in dataset.keys():
        
        #save hh quest data and keys
        data_hh = data_all['hh']
        keys_hh = keys_all['hh']
        del data_all['hh']
        del keys_all['hh']
        
        #get the next non-hh questionnaire
        next_questionnaire = list(data_all.keys())[0]
        data_next = data_all[next_questionnaire]
        keys_next = keys_all[next_questionnaire]
        del data_all[next_questionnaire]
        del keys_all[next_questionnaire]
        
        #merge based on HHID
        data_next['HHID'] = keys_next['HHID']
        data = pd.merge(data_next, data_hh, left_on='HHID', right_index=True, 
                        how='outer', suffixes=['', '_right'])
        
        keys = pd.merge(keys_next, keys_hh, left_on='HHID', right_index=True, 
                        how='outer', suffixes=['', '_right'])
        
        data.drop(['HHID'], axis=1, inplace=True)
        
        if drop_na_index:
            indices = np.where(~data.index.isna())[0]
            data = data.iloc[indices, :]
            keys = keys.iloc[indices, :]
    
    #if hh is not present, we initialize the data and keys with the
    #data and keys of the first questionnaire
    else:
        next_questionnaire = list(data_all.keys())[0]
        data = data_all[next_questionnaire]
        keys = keys_all[next_questionnaire]
        del data_all[next_questionnaire]
        del keys_all[next_questionnaire]
        
    #merge the remaining questionnaires based on HLID
    next_questionnaires = list(data_all.keys())
    for quest in next_questionnaires:
        data_next = data_all[quest]
        keys_next = keys_all[quest]
        
        data = pd.merge(data, data_next, 
                        left_index=True, right_index=True, 
                        how='outer', suffixes = ('', '_right'))
        
        keys = pd.merge(keys, keys_next, 
                        left_index=True, right_index=True, 
                        how='outer', suffixes = ('', '_right'))
    
    #fix indices and columns not anymore needed
    # data.index = data['HLID']
    # data.drop(['HLID'], axis=1, inplace=True)
    
    keys.index=keys['HLID']
    
    #remove duplicate cols
    cols_to_be_removed = []
    for C in data.columns:
        if C.endswith('_right'):
            cols_to_be_removed.append(C)
    
    data.drop(cols_to_be_removed, axis=1, inplace = True)
    
    cols_to_be_removed = []
    for C in keys.columns:
        if C.endswith('_right'):
            cols_to_be_removed.append(C)
    
    keys.drop(cols_to_be_removed, axis=1, inplace = True)
    
    #TODO: remove indices ending with '-1'    
    return(data, keys)

def merge_questionnaires_manual(df1, df2, key1, key2=None):
    '''
    Join (outer) two dataframes df1 and df2, based on key1 and key2
    If the same column is present in both df1 and df2, it attempts to keep the
    column with less nans.
    
    Parameters
    ----------
    df1 : pandas.DataFrame
        First dataframe
    df2 : pandas.DataFrame
        Second dataframe
    key1 : str
        column to be used as key for the first dataframe
    key2 : str, oprional
        If specifiedm column to be used as key for the second dataframe.
        Otherwise key2 = key1
        
    Returns
    -------
    pandas.DataFrame
        Merged dataframe
    '''

    
    if key2 is None:
        key2 = key1
    
    common_cols = df2.columns[[C in df1.columns for C in df2.columns]]
    
    #check which df have more/less nans
    cols_from_1 = []
    cols_from_2 = []
    for C in common_cols:
        
        if np.dtype(df1[C]) == 'O':
            if C != key2:
                cols_from_1.append(C)
        else:
            n_1 = sum(np.isnan(df1[C].values))
            n_2 = sum(np.isnan(df2[C].values))
            if n_2 < n_1:
                cols_from_2.append(C)
            else:
                cols_from_1.append(C)

    if len(cols_from_2)>0:
        df1 = df1.drop(cols_from_2, axis=1)
    
    if len(cols_from_1)>0:
        df2 = df2.drop(cols_from_1, axis=1)
            
    df_merged = pd.merge(df2, df1, how='outer', left_on=key1, right_on=key2, sort=True)
    
    return(df_merged)