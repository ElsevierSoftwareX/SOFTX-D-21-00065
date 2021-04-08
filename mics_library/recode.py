import pandas as pd
import os

def create_recoding_dict(recod_dir):
    '''
    Create a dictionary with information about how to recode the numerical 
    values in a MICS dataset, starting from .csv files. 
    The dictionary can then be used when loading a dataset to homogenize the
    meaning of each numerical value across countries (/or mics round).
    
    This function requires csv files to follow a specific format:
    A csv file should be ceated starting from pandas.DataFrame resulting 
    from the mics_library.preview.check_values, where cells 
    include the numerical values to be used for the recoding,
    instead of the description each numerical value for each country.
    
    E.g. (recode all education levels to 0, 
          except for Secondary, which is recoded as 1):
        
        Dataframe resulting from check_values:
            
    |                   | label                       | used_indicator | 1               | 2                  | 3                               | 4                    | 5                            | 9          |
    |-------------------|-----------------------------|----------------|-----------------|--------------------|---------------------------------|----------------------|------------------------------|------------|
    | Bangladesh        | Education of household head | HELEVEL        | None            | Primary incomplete | Primary complete                | Secondary incomplete | Secondary complete or higher | Missing/DK |
    | Pakistan (Punjab) | Education of household head | HELEVEL        | None/pre-school | Primary            | Middle                          | Secondary            | Higher                       | Missing/DK |
    | Nigeria           | Education of household head | HELEVEL        | None            | Primary            | Secondary / Secondary-technical | Higher               | Non-formal                   | Missing/DK |
    
    
        Compatble dataframe with recoding values:
    |                   | label                       | used_indicator | 1 | 2 | 3 | 4 | 5 | 9 |
    |-------------------|-----------------------------|----------------|---|---|---|---|---|---|
    | Bangladesh        | Education of household head | HELEVEL        | 0 | 0 | 0 | 0 | 1 |   |
    | Pakistan (Punjab) | Education of household head | HELEVEL        | 0 | 0 | 0 | 1 | 0 |   |
    | Nigeria           | Education of household head | HELEVEL        | 0 | 0 | 1 | 0 | 0 |   |
    
    
    
    Parameters
    ----------
    recode_dir : str
        Path to the folder containing the recoding files. 
        The name of a csv file should be the acronym it recodes.
        Files should be included in sub-folders that indicate the questionnaire:
        
        E.g.
        recode_dir
        ├── ch
        │   └── EC1.csv
        ├── hh
        │   └── HELEVEL.csv
        └── hl
    
    Returns
    -------
    dict : encoding_dict
        { country : { old_value1 : new_value1,
                      old_value2 : new_value2,
                      ...
                    }
        }
        for each country: 
        old_value: value stored in the dataset
        new_value: value that will substitute the old_value
    
    '''
    recoding_dict = {}
    questionnaires = os.listdir(recod_dir)
    for quest in questionnaires:
        indicators = os.listdir(os.path.join(recod_dir, quest))
        if len(indicators)>0:
            recoding_dict[quest] = {}

        for indicator in indicators:
            #TODO: if indicator already exists in the recoding_dictionary?
            recoding_dict[quest].update(_create_encoding_indicator(os.path.join(recod_dir, quest, indicator)))
    return(recoding_dict)

def _create_encoding_indicator(csvfile):
    '''
    Create a dictionary with information about how to recode the numerical 
    values in a questionnaire. 
    The dictionary can then be used when loading a dataset to homogenize the
    meaning of each numerical value across countries (/or mics round).
    
    The dictionary is created starting from a formatted csv file.
    The csv file should be ceated starting from a csv file resulting from the 
    mics_library.preview.check_values, where cells 
    include the numerical values to be used for the recoding,
    instead of the description each numerical value for each country.
    
    Parameters
    ----------
    csvfile : str
        Path to the csv file containing the recoding
    
    Returns
    -------
    dict : encoding_dict
        { country : { old_value1 : new_value1,
                      old_value2 : new_value2,
                      ...
                    }
        }
        for each country: 
        old_value: value stored in the dataset
        new_value: value that will substitute the old_value
    
    '''
    #TODO create example
    
    csv_filename = os.path.split(csvfile)[1]
    acronym = csv_filename.split('.')[0]
    data_csv = pd.read_csv(csvfile, index_col = 0)
    
    data_csv.drop(['label', 'used_indicator'], axis = 1, inplace=True)
    
    encoding_dictionary_indicator = {}
    for country in data_csv.index:
        data_country = data_csv.loc[[country],:]
#        data_country.dropna(axis=1, inplace=True)
        
        dict_country = {}
        for x in data_country.columns:
            if x.isnumeric():
                dict_country[float(x)] = data_country.loc[:,x].values[0]
            else:
                dict_country[x] = data_country.loc[:,x].values[0]
                 
        encoding_dictionary_indicator[country] = dict_country
    
    return({acronym: encoding_dictionary_indicator})