import pandas as pd
import pyreadstat
import os
from .utils import get_countryname
from .loaders import get_dict
from .swap_indicators import merge_swap_indicators
from . import get_rootdir
import numpy as np

def screen(micsround, countries=None, questionnaires=None, ignorecase=True):
    '''
    Get a quick summary of the data available in a MICS's round.
    
    Return a dictionary with questionnaires as keys and pandas' dataframes as values: 
        {'questionnaire' :dataframe}
    The dataframe lists the items in the questionnaire,
    with the description and number of countries.
    
    Parameters
    ----------
    miscround : int
        the round of the mics
    countries: list, optional
        List of countries to consider (not implemented yet).
        Default None = all available countries
    questionnaires: list, optional
        Which questionnaires to consider
        'hh', 'hl', 'ch', 'wm', 'mn', 'bh' are valid questionnaires
        Default None = 'hh', 'hl', 'ch', 'wm', 'mn', 'bh'
    ignorecase: boolean, optional
        Whether to consider uppercase and lowercase acronyms the same. 
        Default True
    
    Returns
    -------
    dictionary
        Dictionary like {'hh': hh_dataframe, ...}
    '''
    
    MICS_ROOTDIR = get_rootdir()
    DATADIR = f'{MICS_ROOTDIR}/MICS{micsround}'
    
    assert countries is None, "Country selection not implemented yet"
    countries = os.listdir(DATADIR)
    
    if questionnaires is None:
        questionnaires = ['hh', 'hl', 'ch', 'wm', 'mn', 'bh']
        
    questionnaire_dict = {}
    
    for questionnaire in questionnaires:
        
        #this dict will contain the info for each indicator in any country
        indicators_dict = {}
        
        #open the questionnaire for all countries
        for country in countries:
            countryname = get_countryname(micsround, country)
            
            if f'{questionnaire}.sav' in os.listdir(f'{DATADIR}/{country}'):
                _, meta = pyreadstat.read_sav(f'{DATADIR}/{country}/{questionnaire}.sav', metadataonly=True)
                
                #get the dictionary of label and values of all indicators in the questionnaire
                dict_quest = get_dict(meta)
                
                #update the indicators_dict
                for indicator in dict_quest.keys():
                    label = dict_quest[indicator]['label']
                    
                    if ignorecase: #set acronym to uppercase
                        indicator = indicator.upper()
                    
                    if indicator not in indicators_dict.keys(): #first country: create the list
                        indicators_dict[indicator] = {'labels': [label], 'countries': [countryname]}
                    else:
                        indicators_dict[indicator]['labels'].append(label) # add the new label
                        indicators_dict[indicator]['countries'].append(countryname) # current country
    
        #%
        df_ind = []
        #get the most common labels and number of countries
        for indicator in indicators_dict.keys():
            labels = np.array(indicators_dict[indicator]['labels'])
            
            #remove all (?) strange values
            labels = labels[[isinstance(x, str) for x in labels]]
            
            if len(labels)>0: #there is at least one country
                
                #get the unique labels with counts
                uniquelabels, counts = np.unique(labels, return_counts=True)
                
                #get the most common label
                common_label = uniquelabels[np.argmax(counts)]

            else:
                common_label = 'None'
                
            n_countries = len(labels)
            df_ind.append(pd.DataFrame({'label':common_label, 'ncountries':n_countries}, index = [indicator]))

        #TODO: SORT INDICATORS BY NUMBER OF COUNTRIES
        #merge all indicators df into one
        if len(df_ind)>0:
            df_questionnaire = pd.concat(df_ind, axis=0)
            questionnaire_dict[questionnaire] = df_questionnaire

    return(questionnaire_dict)
    
def check_values(micsround, indicators, swap_indicators = {}, countries=None, ignorecase=True):
    '''
    Check the label and values of target indicators for each country
    
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
    swap_indicators : dict
        { questionnaire : { country : { new_name_indic1 : name_indic1, ...}}}
        Dictionary used to define how some indicator names of some countries
        should be changed to comply with the names used in the majority of the
        countries.
    countries: list, optional
        List of countries to consider (not implemented yet).
        Default None = all available countries
    ignorecase: boolean, optional
        Whether to consider uppercase and lowercase acronyms the same. 
        Default True
    
    Returns
    -------
    dictionary
        Dictionary like {'questionnaire': {'indicator_name': dataframe, ...}
        where dataframe is a pandas' dataframe with the description and 
        values of the indicators for each country.
    '''
    MICS_ROOTDIR = get_rootdir()
    DATADIR = os.path.join(MICS_ROOTDIR, f'MICS{micsround}')
    
    assert countries is None, "Country selection not implemented yet"
    countries = os.listdir(DATADIR)
    
    questionnaires = list(indicators.keys())
    
    swap_indicators = merge_swap_indicators(micsround, swap_indicators)
    
    questionnaire_dict = {}
    
    for questionnaire in questionnaires:
        
        #get indicators of the questionnaire to process
        indicators_questionnaire = indicators[questionnaire]
        
        #get swap indicators for this questionnaire
        swap_indicators_questionnaire = swap_indicators[questionnaire] if questionnaire in swap_indicators else {}  

        #add upper and lower case acronyms        
        if ignorecase:
            indicators_questionnaire_upper = [x.upper() for x in indicators_questionnaire]
            indicators_questionnaire_lower = [x.lower() for x in indicators_questionnaire]
        
            indicators_questionnaire = indicators_questionnaire_upper + indicators_questionnaire_lower

        #dict that will contain all the info for each indicator in the questionnaire
        indicators_info = {} 
        
        #process all countries
        for country in countries:
            #get country name
            countryname = get_countryname(micsround, country)
            
            #get swap_indicators of this country
            swap_indicators_country = swap_indicators_questionnaire[countryname] if countryname in swap_indicators_questionnaire else {}
            
            #scan the list of the indicators and substitute with the swapped
            indicators_to_be_used = []
            for ind_target in indicators_questionnaire:
                if ind_target in swap_indicators_country.keys():
                    ind_used = swap_indicators_country[ind_target]
                    indicators_to_be_used.append(ind_used)
                else:
                    indicators_to_be_used.append(ind_target)
            
            if f'{questionnaire}.sav' in os.listdir(os.path.join(DATADIR, country)):
                _, meta = pyreadstat.read_sav(os.path.join(DATADIR, country, f'{questionnaire}.sav'), 
                                              usecols = indicators_to_be_used)
                
                #get the dictionary of label and values of all indicators in the questionnaire
                dict_quest = get_dict(meta, ignorecase)
                
                #create a reverse swap dictionary to obtain the original target indicators
                swap_indicators_country_reverse = dict([(v,k) for (k,v) in swap_indicators_country.items()])
                
                #for each indicator in dict_quest, extract the info and populate dict_info
                for ind_used in dict_quest.keys():
                    if ind_used in swap_indicators_country_reverse:
                        ind_target = swap_indicators_country_reverse[ind_used]
                    else:
                        ind_target = ind_used
                    
                    if ignorecase:
                        ind_target = ind_target.upper()

                    if ind_target not in indicators_info.keys(): #first country: create the list
                        #!!! I use 'ind_target' in the output dict and 'ind_used' to get the info
                        indicators_info[ind_target] = {countryname: {'info': dict_quest[ind_used], 'used_indicator': ind_used}} 
                    else:
                        indicators_info[ind_target][countryname] = {'info': dict_quest[ind_used], 'used_indicator': ind_used}
        
        #process indicator_info and create a dataframe
        dataframe_dict = {}
        
        for indicator in indicators_info.keys():
            
            data_indicator = indicators_info[indicator]
            
            labels_and_indicators = []
            
            legends = {}
            for country in data_indicator.keys():
                data_country= data_indicator[country]
                labels_and_indicators.append([data_country['info']['label'],
                                              data_country['used_indicator']])
                
                data_country_info = data_country['info']
                if 'values' in data_country_info.keys():
                    legends[country] = data_country_info['values']
                
            labels = pd.DataFrame(labels_and_indicators, index = data_indicator.keys())
            labels.columns = ['label', 'used_indicator']
            
            if len(legends)>0:
                legends = pd.DataFrame(legends).transpose()
            
                df_indicator = pd.merge(labels, legends, how = 'outer', left_index=True, right_index=True)
            else:
                df_indicator = labels
            dataframe_dict[indicator] = df_indicator
        
        questionnaire_dict[questionnaire] = dataframe_dict

    return(questionnaire_dict)