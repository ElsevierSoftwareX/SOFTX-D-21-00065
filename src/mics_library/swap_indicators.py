swap_indicators_3 = {'hl' : {'Ukraine': {'HL1':'LN'},
                             'Georgia': {'HL1':'LN'},
                             'Palestinians in Lebanon': {'HL10': '',
                                                         'HL12': ''}},
                     
                     'wm' : {'Burundi': {'LN': 'WM4'},
                             'Mongolia': {'LN': 'HL1'},
                             'Albania': {'LM': 'WMID'},
                             'Palestinians in Lebanon' : {'LN':'WM4'}},
                     
                     'ch' : {'Burundi' : {'LN':'UF4'},
                             'Mongolia' : {'LN':'HL1'},
                             'Albania' : {'LN':'UFID'},
                             'Palestinians in Lebanon' : {'LN':'UF4', 
                                                          'UF6':''},
                             
                             #The name of the question is switched (M<-->F)
                             #but the answer is correct:
                             # 'Yemen': {'BR8AF': 'BR8AM', 'BR8AM': 'BR8AF',
                             #           'BR8BF': 'BR8BM', 'BR8BM': 'BR8BF',
                             #           'BR8CF': 'BR8CM', 'BR8CM': 'BR8CF',
                             #           'BR8DF': 'BR8DM', 'BR8DM': 'BR8DF',
                             #           'BR8EF': 'BR8EM', 'BR8EM': 'BR8EF',
                             #           'BR8FF': 'BR8FM', 'BR8FM': 'BR8FF'}
                             },
                     
                     'hh': {'Nigeria': {'HC9F': 'HC9I'},
                            'Cameroon': {'HC9F': 'HC9H'}}    
                     }

swap_indicators_4 = {'ch': {'Chad': {'EC7DX': 'EC7DC',
                                     'EC7EX': 'EC7EC',
                                     'EC7EY': 'EC7ED'},
                            
                            'Pakistan (Balochistan)': {'EC7DX': 'EC7DC',
                                                       'EC7EX': 'EC7EC',
                                                       'EC7EY': 'EC7ED'},
                                       
                            'Central African Republic': {'EC7DX': 'EC7DC',
                                                         'EC7EX': 'EC7EC',
                                                         'EC7EY': 'EC7ED'},
                                                          
                            'The Gambia': {'EC7DX': 'EC7DC',
                                           'EC7EX': 'EC7EC',
                                           'EC7EY': 'EC7ED'}},
                     
                     'hl': {'Kenya (Mombasa Informal Settlements)': {'ED3': 'ED2',
                                                                     'ED4A':'ED3A'},
                            
                            'Kenya (Nyanza Province)': {'ED3': 'ED2',
                                                        'ED4A':'ED3A'},
                            
                            'Madagascar (South)': {'ED4A': 'ED4AX'},
                            
                            'Nepal (Mid-and Far-Western Regions)': {'ED4A': 'ED4B'},
                            
                            'Mongolia': {'ED4A': 'ED4_A'},
                            
                            'State of Palestine': {'ED4A': 'ED4'}}}

swap_indicators_5 = {'ch' : {'Mexico' : {'LN': 'UF4'}},
                     'hh' : {'Panama' : {'SL9B': 'CD9'}},
                     'hl' : {'Pakistan (Sindh)': {'ED4A': ''},
                             'Nepal': {'ED4A': 'ED4B'}}}

swap_indicators = {3: swap_indicators_3,
                   4: swap_indicators_4,
                   5: swap_indicators_5}


def merge_swap_indicators(micsround, custom_swap_indicators):
    '''
    Merge custom swap indicators with those provided by the mics_library.
        
    '''
    if len(custom_swap_indicators)>0:
        print('Please, consider submitting the custom_swap_indicators to the mics_library developers')
    
    swap_indicators_out = swap_indicators[micsround]
    
    for quest, quest_dict in custom_swap_indicators.items():
        if quest not in swap_indicators_out:
            swap_indicators_out[quest] = {}
        
        for country, country_dict in quest_dict.items():
            if country not in swap_indicators_out[quest]:
                swap_indicators_out[quest][country] = {}
                
            for item_target, item_used in country_dict.items():
                swap_indicators_out[quest][country][item_target] = item_used
        
    return(swap_indicators_out)