from django.shortcuts import render
from django_pandas.io import *
from django.db import IntegrityError
import json


import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz,process
from functools import reduce
from statsmodels import robust as smr
import MySQLdb # drivers for accessing the database through sqlalchemy

from authentication.models import CustomUser


from home.models import (StgMeasuremethod,StgCategoryoption,
    StgDatasource,)
from indicators.models import StgIndicator

from .models import (Facts_DataFrame,CategoryOptions_Validator,
    MeasureTypes_Validator,DataSource_Validator,MissingValuesRemarks,
    Mutiple_MeasureTypes,DqaInvalidDatasourceRemarks,
    DqaInvalidCategoryoptionRemarks,DqaInvalidMeasuretypeRemarks,
    Similarity_Index,DqaInvalidPeriodRemarks,
    DqaExternalConsistencyOutliersRemarks,
    DqaInternalConsistencyOutliersRemarks,DqaValueTypesConsistencyRemarks
    )

 

def load_data_validators(request):
    groups = list(request.user.groups.values_list('user', flat=True))
    user = request.user.id  # get logged in user id for access control
    location = request.user.location.name
    language = request.LANGUAGE_CODE 
    current_user = CustomUser.objects.get(pk=user) # get instance of logged user
    
    # -----------------------------------Start Save Data Validation DataFrames---------------------------------------------------------
    # Create data source dataframe and save it into the database into measure types model 
    MesureTypeValid  = pd.DataFrame() # initialize an empty dataframe
    DataSourceValid  = pd.DataFrame() # initialize an empty dataframe
    CategoryOptionValid  = pd.DataFrame() # initialize an empty dataframe
    try:
        MesureTypeValid = pd.read_excel('Datasets/Excel_Format/Mesuretype.xls')
        MesureTypeValid.rename({'IndicatorId':'afrocode','Indicator Name':'indicator_id', 
                'measurementmethod':'measure_type_id','measuremethod_id':'measuremethod_id'},
                axis=1, inplace=True)              
        
        measuretypes = MesureTypeValid.to_records(index=True)
        try:
            measuretypes = [
                MeasureTypes_Validator(
                    afrocode=record['afrocode'],
                    indicator= StgIndicator.objects.get(
                        pk=record['indicator_id']), # FK instance of StgIndicator
                    measure_type=StgMeasuremethod.objects.get(
                        pk=record['measure_type_id']), # FK instance of StgMeasuremethod
                    measuremethod_id=record['measuremethod_id'],
                    user = current_user
                )
                for record in measuretypes    
            ]
            # BEHAVIOUR -ignore_conflicts=True allows records to be auto-inserted if not EXIST!  
            records = MeasureTypes_Validator.objects.bulk_create(
                measuretypes,ignore_conflicts=True,)    
        except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
            pass 
        except: # ignore othe database related errors
            print('Unknown Error has occured') 
    except: # ignore errors relating to missing Excel file
        pass                     


    # # Create data source dataframe and save it into the database into the datasource model
    try:
        DataSourceValid = pd.read_excel('Datasets/Excel_Format/Datasource.xls')  
        DataSourceValid.rename(
            {'IndicatorId':'afrocode','Indicator Name':'indicator_id', 
            'DataSource':'datasource_id','DatasourceId':'datasourceid'},
            axis=1, inplace=True)   
        try: 
            datasources = DataSourceValid.to_records(index=True)
            datasources = [
                DataSource_Validator(
                    afrocode=record['afrocode'],
                    indicator= StgIndicator.objects.get(
                        pk=record['indicator_id']), # FK instance of StgIndicator
                    datasource=StgDatasource.objects.get(
                        pk=record['datasource_id']), # FK instance of StgMeasuremethod
                    datasourceid=record['datasourceid'],
                    user = current_user
                )
                for record in datasources    
            ]
            records = DataSource_Validator.objects.bulk_create(
                datasources,ignore_conflicts=True,)    
        except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
            pass 
        except: # ignore othe database related errors
            print('Unknown Error has occured') 
    except: # ignore errors relating to missing Excel file
        pass                        


    # Create data source dataframe and save it into the database into the datasource model
    try:
        CategoryOptionValid = pd.read_excel('Datasets/Excel_Format/Categoryoption.xls')
        CategoryOptionValid.rename({'IndicatorId':'afrocode','Indicator Name':'indicator_id', 
                'Category':'categoryoptionid','CategoryId':'categoryoption_id'},axis=1, inplace=True)   
        try: 
            categoryoptions = CategoryOptionValid.to_records(index=True)
            categoryoptions = [
                CategoryOptions_Validator(
                    afrocode=record['afrocode'],
                    indicator= StgIndicator.objects.get(
                        pk=record['indicator_id']), # FK instance of StgIndicator
                    categoryoption=StgCategoryoption.objects.get(
                        pk=record['categoryoption_id']), # FK instance of StgMeasuremethod
                    categoryoptionid=record['categoryoptionid'],
                    user = current_user
                )
                for record in categoryoptions    
            ]
            records = CategoryOptions_Validator.objects.bulk_create(
                categoryoptions,ignore_conflicts=True,)    
        except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
            pass 
        except: # ignore othe database related errors
            print('Unknown Error has occured') 
    except: # ignore errors relating to missing Excel file
        pass                         
    
    # import pdb; pdb.set_trace()
    if not MesureTypeValid.empty or not DataSourceValid.empty or not CategoryOptionValid.empty:
        success = "Data source, category options and measure types validation lookup \
            tables created and saved into the Database"
    else:
        success ="Sorry. The validators has not been validated"     
    context = {              
        'success':success,
    }
    return render(request,'data_quality/home.html',context)


def check_data_quality(request):
    groups = list(request.user.groups.values_list('user', flat=True))
    user = request.user.id  # get logged in user id for data-level access control
    location = request.user.location.name
    language = request.LANGUAGE_CODE 
    location_level = request.user.location.locationlevel_id    
    current_user = CustomUser.objects.get(pk=user) # get instance of logged user

    # ----------------------------------End primary data validation dataFrames---------------------------------------------------------
    facts_df = pd.DataFrame() # initialize the facts dataframe with a null value
    data = pd.DataFrame()
    
    qs = Facts_DataFrame.objects.all().order_by('indicator_name')
    if request.user.is_superuser:
        qs=qs # show all records if logged in as super user

    elif user in groups: # return records on if the user belongs to the group
        qs=qs.filter(location=location)
    else: # return records belonging to logged in user
        qs=qs.filter(user=user) 
    
    if len(qs) >0: # create dataframe based on logged in user
        facts_df = qs.to_dataframe(['fact_id', 'indicator_name', 'location',
                'categoryoption','datasource','measure_type',
                'value','period'],index='fact_id')
                
        data=facts_df.rename({'fact_id':'fact_id', 'indicator_name':'Indicator Name', 
            'location':'Country','categoryoption':'CategoryOption',
            'datasource':'DataSource','measure_type':'measure type',
            'value':'Value','period':'Year'},axis=1)

        # -----------------------------------Misscellanious algorithm - Count Data Source and measure Type For Each Indicators-----
        missing_numeric = pd.DataFrame() # initialize numeric dataframe with empty values
        missing_string = pd.DataFrame() # initialize string dataframe with empty values
        missing_values_df = pd.DataFrame() 
        
        numeric_data = data[data['measure type']!= "String"].copy()
        missing_numeric = numeric_data[numeric_data.Value.isnull()].copy()
        
        string_data = data[data['measure type']== "String"].copy()
        missing_string = string_data[string_data.Value.isnull()].copy()
        
        if not missing_numeric.empty:
            missing_numeric["Check_Missing_Numeric_Value"] = "Missing Numeric Value"
            missing_numeric_df=missing_numeric.rename({'Indicator Name':'indicator_name',
                'Country':'location','CategoryOption':'categoryoption',
                'DataSource':'datasource','measure type':'measure_type',
                'Year':'period','Value':'value','Year':'period',
                'Check_Missing_Numeric_Value':'remarks'},axis=1)  

        if not missing_string.empty:
            missing_string["Check_Missing_String_Value"] = "Missing String Value"
            missing_string_df=missing_string.rename({'Indicator Name':'indicator_name',
                'Country':'location','CategoryOption':'categoryoption',
                'DataSource':'datasource','measure type':'measure_type',
                'Year':'period','Value':'value','Year':'period',
                'Check_Missing_String_Value':'remarks'},axis=1)  

            missing_values_df =pd.concat((missing_numeric_df,missing_string_df),axis = 0)
            values_checker = missing_values_df.to_records(index=True)     
            try:
                missingvalues = [
                    MissingValuesRemarks(
                        id=record['fact_id'],
                        indicator_name=record['indicator_name'],
                        location=record['location'],
                        categoryoption=record['categoryoption'],
                        datasource=record['datasource'],
                        measure_type=record['measure_type'],
                        value=record['value'],
                        period=record['period'],
                        remarks=record['remarks'],   
                        user = current_user,               
                    )
                    for record in values_checker
                ]
                records = MissingValuesRemarks.objects.bulk_create(
                    missingvalues,ignore_conflicts=True,)
            except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                pass 
            except: # ignore othe database related errors
                print('Unknown Error has occured')         
               
        
        multi_source_measures_df = pd.DataFrame()
        multimeasures_df = pd.DataFrame()

        DataSourceNumber = data.groupby(['Country', 'Indicator Name'], as_index=False).agg({"DataSource": "nunique"})
        MultipleDataSources = DataSourceNumber[DataSourceNumber.DataSource>1] # indicator with multiple sources
        
        # Count each country indicators with more than one measure type
        MesureTypeByIndicatorCounts = data.groupby(['Country', 'Indicator Name'], as_index=False).agg(
            {"measure type": "nunique"})

        MultipleMesureTypeIndicator = MesureTypeByIndicatorCounts[
            MesureTypeByIndicatorCounts['measure type']>1]
        MultipleMesureTypeIndicator=MultipleMesureTypeIndicator.rename({'Indicator Name':'indicator_name',
            'Country':'location','measure type':'count',},axis=1)  
        
        if not MultipleMesureTypeIndicator.empty:           
            # Insert comments and save indicators with more than one measure type (Didier's data 1)
            for index, row in MultipleMesureTypeIndicator.iterrows():
                data.loc[(data['Country'] == row['location']) & (
                    data['Indicator Name'] == row[
                        'indicator_name']),'Check_Mesure_Type'] = "Indicator with multiple mesure types"                
            multimeasures_df = data[data.Check_Mesure_Type.str.len() > 0] # Didier's data1
            
            multi_measures_df=multimeasures_df.rename({'Indicator Name':'indicator_name',
                'Country':'location','CategoryOption':'categoryoption',
                'DataSource':'datasource','measure type':'measure_type',
                'Year':'period','Value':'value','Year':'period',
                'Check_Mesure_Type':'remarks1'},axis=1)       
       
            # Count each country indicators with more than one measure type per data source
            NumberMesureTypeByIndicatorPerDS = data.groupby(
                ['Country', 'Indicator Name', 'DataSource'], as_index=False).agg({"measure type": "nunique"})
            MultipleMesureTypeIndicatorPerDS = NumberMesureTypeByIndicatorPerDS[
                NumberMesureTypeByIndicatorPerDS['measure type']>1]
            
            if not MultipleMesureTypeIndicatorPerDS.empty:           
                for index, row in MultipleMesureTypeIndicatorPerDS.iterrows():
                    data.loc[(data['Country'] == row['Country']) & (
                        data['Indicator Name'] == row['Indicator Name']) & (
                            data['DataSource'] == row[
                                'DataSource']),'Check_Mesure_Type'] = "Multiple mesure type for this data source "
                multi_source_measuresdf = data.loc[data.Check_Mesure_Type.str.len() > 0] # Didier's data2

                multi_source_measures_df=multi_source_measuresdf.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Year':'period','Value':'value',
                    'Year':'period','Check_Mesure_Type':'remarks'},axis=1)    
                  
            measures_checker_df = pd.concat((multi_measures_df, multi_source_measures_df), axis = 1)
            multimeasures = measures_checker_df.loc[:,~measures_checker_df.T.duplicated(
                keep='last')]
            multimeasures_df=multimeasures.drop('remarks1', axis=1) # drop one of the remarks from concarenated dataframe
            multimeasuresdf = multimeasures_df.copy()
            measures_checker = multimeasuresdf.to_records(index=True)
                
            try:
                multimeasures = [
                    Mutiple_MeasureTypes(
                        id=record['fact_id'],
                        indicator_name=record['indicator_name'],
                        location=record['location'],
                        categoryoption=record['categoryoption'],
                        datasource=record['datasource'],
                        measure_type=record['measure_type'],
                        value=record['value'],
                        period=record['period'],
                        # counts=record['counts'],
                        remarks=record['remarks'],   
                        user = current_user,               
                    )
                    for record in measures_checker
                ]
                records = Mutiple_MeasureTypes.objects.bulk_create(
                    multimeasures,ignore_conflicts=True,)
            except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                pass 
            except: # ignore othe database related errors
                print('Unknown Error has occured') 
        

    # -------------------------------Import algorithm 1 - indicators with wrong measure types--------------------------
        valid_datasources_qs = DataSource_Validator.objects.all().order_by('afrocode')

        data.drop('Check_Mesure_Type', axis=1, inplace=True) # remove period remarks from the facts dataframe     
        bad_datasource = pd.DataFrame()
        if len(qs) >0:
            DataSourceValid = valid_datasources_qs.to_dataframe(['id', 'afrocode', 'indicator',
                'datasource','datasourceid'],index='id')
    
            DataSourceValid.rename({'indicator':'Indicator Name','datasource':'DataSource',
                'datasourceid':'DatasourceId',},axis=1, inplace=True)
            UniqueIndicatorV = DataSourceValid['Indicator Name'].unique().tolist()

            dataWDS = pd.DataFrame(columns=data.columns.tolist()) # create an emplty list of columns from facts dataset
            for indicator in UniqueIndicatorV: # iterate through the data source list of indicators 
                ValidDataSource = DataSourceValid[
                    DataSourceValid['Indicator Name']==indicator]['DataSource'] # get all datasources for the indicator                
                ValidDataSource = ValidDataSource.unique().tolist() # create a list of valid sources [country, who/gho,nis]
                ActualDataSource = data[data['Indicator Name']==indicator]['DataSource'] # get all data sources from dataset
                ActualDataSource = ActualDataSource.unique().tolist()
                WDS = list(set(ActualDataSource) - set(ValidDataSource))
                if(len(WDS)!=0): # check whether the set diffrence is zero
                    for ds in WDS:
                        IWWDS = data[(data['Indicator Name']==indicator) & (
                            data['DataSource']==ds)] # indicator with wrong data source
                        dataWDS = pd.concat((dataWDS,IWWDS), axis = 0,ignore_index = True) # append rows (axis=0) into the empty dataframe
            
            if not dataWDS.empty:
                dataWDS.loc[:,'Check_Data_Source'] = 'This data source is not applicable to this indicator'
                bad_datasource = dataWDS # Didier's data3: create dataframe for wrong data sources
                
                bad_datasource_df=bad_datasource.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Value':'value','Year':'period',
                    'Check_Data_Source':'check_data_source'},axis=1)  
                
                datasource_checker = bad_datasource_df.to_records(index=True)
                try:        
                    datasources = [
                        DqaInvalidDatasourceRemarks(
                            indicator_name=record['indicator_name'],
                            location=record['location'],
                            categoryoption=record['categoryoption'],
                            datasource=record['datasource'],
                            measure_type=record['measure_type'],
                            value=record['value'],
                            period=record['period'],
                            check_data_source=record['check_data_source'], 
                            user = current_user

                        )
                        for record in datasource_checker
                    ]
                    # BEHAVIOUR -ignore_conflicts=True allows records to be auto-inserted if not EXIST!  
                    records = DqaInvalidDatasourceRemarks.objects.bulk_create(
                        datasources,ignore_conflicts=True,)
                except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                    pass 
                except: # ignore othe database related errors
                    print('Unknown Error has occured') 


        # -------------------------------Import algorithm 2 - indicators with wrong category options--------------------------
        valid_categoryoptions_qs = CategoryOptions_Validator.objects.all().order_by('afrocode')
        categoryoption_df = pd.DataFrame()
        measuretypes_df = pd.DataFrame()
        if len(qs) >0:
            CategoryOptionValid = valid_categoryoptions_qs.to_dataframe(['id', 'afrocode', 'indicator',
                'categoryoption','categoryoptionid'],index='id')
            CategoryOptionValid.rename({'indicator':'Indicator Name','categoryoption':'Category',
               'categoryoptionid':'CategoryId', },axis=1, inplace=True)
            UniqueIndicatorV = CategoryOptionValid['Indicator Name'].unique().tolist()
            
            dataWCO = pd.DataFrame(columns=data.columns.tolist())
            for indicator in UniqueIndicatorV:               
                ValidCO = CategoryOptionValid[CategoryOptionValid['Indicator Name']==indicator]['Category'] # this is ok
                ValidCO = ValidCO.unique().tolist() # return ['Male', 'Female', 'Both sexes (male and female)']
                ActualCO = data[data['Indicator Name']==indicator]['CategoryOption'] # get related categoryoption from dataset for this indicator
                ActualCO = ActualCO.unique().tolist()
                WCO = list(set(ActualCO) - set(ValidCO))
                if(len(WCO)!=0):
                    for co in WCO:
                        IWWCO = data[(data['Indicator Name']==indicator) & (data['CategoryOption']==co)]
                        dataWCO = pd.concat((dataWCO,IWWCO), axis = 0,ignore_index = True) # append rows (axis=0) into the empty dataframe
            
            if not dataWCO.empty:       
                dataWCO.loc[:,'Check_Category_Option'] = 'This category option is not applicable to this indicator'            
                categoryoption_df = dataWCO # Didier's data4: Create dataframe with check measure type remarks column
                            
                bad_categoryoption_df=categoryoption_df.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Value':'value','Year':'period',
                    'Check_Category_Option':'check_category_option'},axis=1)  
                
                categoryoptions_checker = bad_categoryoption_df.to_records(index=True)
                try:    
                    categoryoptions = [
                        DqaInvalidCategoryoptionRemarks(
                            indicator_name=record['indicator_name'],
                            location=record['location'],
                            categoryoption=record['categoryoption'],
                            datasource=record['datasource'],
                            measure_type=record['measure_type'],
                            value=record['value'],
                            period=record['period'],
                            check_category_option=record['check_category_option'],
                            user = current_user    
                        )
                        for record in categoryoptions_checker
                    ]
                    records = DqaInvalidCategoryoptionRemarks.objects.bulk_create(
                        categoryoptions,ignore_conflicts=True,)
                except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                    pass 
                except: # ignore othe database related errors
                    print('Unknown Error has occured') 
                

        # -------------------------------Import algorithm 3 - indicators with wrong measure types--------------------------
        valid_measures_qs = MeasureTypes_Validator.objects.all().order_by('afrocode')
        if len(qs) >0:
            MesureTypeValid = valid_measures_qs.to_dataframe(['id', 'afrocode', 'indicator',
                'measure_type','measuremethod_id'],index='id')
            MesureTypeValid.rename({'indicator':'Indicator Name','measure_type':'measure type',
                'measuremethod_id':'measuremethodid',},axis=1, inplace=True)

            UniqueIndicatorV = MesureTypeValid['Indicator Name'].unique().tolist()
            dataWMT = pd.DataFrame(columns=data.columns.tolist())
            
            for indicator in UniqueIndicatorV:
                ValidMT = MesureTypeValid[MesureTypeValid['Indicator Name']==indicator]['measure type'] # get valid measure types
                ValidMT = ValidMT.unique().tolist()
                ActualMT = data[data['Indicator Name']==indicator]['measure type']
                ActualMT = ActualMT.unique().tolist()
                WMT = list(set(ActualMT) - set(ValidMT))
                if(len(WMT)!=0):
                    for mt in WMT:
                        IWWMT = data[(data['Indicator Name']==indicator) & (data['measure type']==mt)]
                        dataWMT = pd.concat((dataWMT,IWWMT), axis = 0,ignore_index = True) # append rows (axis=0) into the empty dataframe
            
            if not dataWMT.empty:                   
                dataWMT.loc[:,'Check_Mesure_Type'] = 'This mesure type is not applicable to this indicator'
                measuretypes_df = dataWMT # Didier's data5 Create dataframe with check measure type remarks column
                
                bad_measuretype_df=measuretypes_df.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Value':'value','Year':'period',
                    'Check_Mesure_Type':'check_mesure_type'},axis=1)  
            
                measures_checker = bad_measuretype_df.to_records(index=True)
                try:    
                    measuretypes = [
                        DqaInvalidMeasuretypeRemarks(
                            indicator_name=record['indicator_name'],
                            location=record['location'],
                            categoryoption=record['categoryoption'],
                            datasource=record['datasource'],
                            measure_type=record['measure_type'],
                            value=record['value'],
                            period=record['period'],
                            check_mesure_type=record['check_mesure_type'],                   
                            user = current_user    
                        )
                        for record in measures_checker
                    ]
                    records = DqaInvalidMeasuretypeRemarks.objects.bulk_create(
                        measuretypes,ignore_conflicts=True,)
                except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                    pass 
                except: # ignore othe database related errors
                    print('Unknown Error has occured') 
   

        # -------------------------------------Start of comparing indicators for similarity score----------------------------        
        UniqueInd = data['Indicator Name'].unique()
        _list_comparison_fullname = []
        _list_entry_fullname = []
        _list_entry_score = []
        for i_dataframe in range(len(UniqueInd)-1):
            comparison_fullname = UniqueInd[i_dataframe]
            for entry_fullname, entry_score in process.extract(comparison_fullname, 
                # NB: fuzz.token_sort_ratio ratio gives higher scores compared to ratio fuzz.ratio
                UniqueInd[i_dataframe+1::],scorer=fuzz.token_sort_ratio): 
                if entry_score >=60:
                    _list_comparison_fullname.append(comparison_fullname) #append* inserts an element to the list 
                    _list_entry_fullname.append(entry_fullname)
                    _list_entry_score.append(entry_score)
                
        CheckIndicatorNameForSimilarities = pd.DataFrame(
            {'IndicatorName':_list_entry_fullname,
            'SimilarIndicator':_list_comparison_fullname,
            'Score':_list_entry_score})   
        Check_similarities=CheckIndicatorNameForSimilarities.rename(
            {'IndicatorName':'source_indicator','SimilarIndicator':'similar_indicator',
            'Score':'score'},axis=1)            
        
        Check_similarities.sort_values(by=['score'],inplace=True,ascending=False)   
        similarities_checker = Check_similarities.to_records(index=True)
        try:    
            similarities = [
                Similarity_Index(
                    source_indicator=record['source_indicator'],
                    similar_indicator=record['similar_indicator'],
                    score=record['score'],                  
                    user = current_user    
                )
                for record in similarities_checker
            ]
            records = Similarity_Index.objects.bulk_create(
                similarities,ignore_conflicts=True,) 
        except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
            pass 
        except: # ignore othe database related errors
            print('Unknown Error has occured') 
        # -------------------------------------End of comparing indicators for similarity score----------------------------             


        # -------------------------------Start of miscellanious algorithms - Year verification -----------------------------------
        MultipleYearTypeIndicator = pd.DataFrame()
        dataWithSelectedColumns = data[['Country', 'Indicator Name', 'DataSource', 'Year']]
        dataWithSelected = dataWithSelectedColumns.copy() # create a copy of the dataframe
        
        dataWithSelected['CYear'] = dataWithSelected['Year'].apply(len) #count characters in year string

        NumberYearTypeIndicator = dataWithSelected.groupby(
            ['Country', 'Indicator Name', 'DataSource'], as_index=False).agg({"CYear": "nunique"})
        MultipleYearTypeIndicator = NumberYearTypeIndicator[NumberYearTypeIndicator['CYear']>1]
        
        if not MultipleYearTypeIndicator.empty: # check whether the dataframe is empty
            for index, row in MultipleYearTypeIndicator.iterrows():
                data.loc[(data['Country'] == row['Country']) & (
                    data['Indicator Name'] == row['Indicator Name']) & (
                        data['DataSource'] == row[
                            'DataSource']),'Check_Year'] ="This indicator has range and single year "
            periods_df = data[data.Check_Year.str.len() > 0] # Didier's data6
            bad_periods_df=periods_df.rename(
                {'Indicator Name':'indicator_name','Country':'location',
                'CategoryOption':'categoryoption','DataSource':'datasource',
                'measure type':'measure_type','Value':'value','Year':'period',
                'Check_Year':'check_year'},axis=1)     
            
        data.drop('Check_Year', axis=1, inplace=True) # remove period remarks from the facts dataframe
        periods_checker = bad_periods_df.to_records(index=True)
        try:    
            periods = [           
                DqaInvalidPeriodRemarks(
                    indicator_name=record['indicator_name'],
                    location=record['location'],
                    categoryoption=record['categoryoption'],
                    datasource=record['datasource'],
                    measure_type=record['measure_type'],
                    value=record['value'],
                    period=record['period'],
                    check_year=record['check_year'],                   
                    user = current_user    
                )
                for record in periods_checker
        ]
            records = DqaInvalidPeriodRemarks.objects.bulk_create(
                periods,ignore_conflicts=True,)
        except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
            pass 
        except: # ignore othe database related errors
            print('Unknown Error has occured') 


        # --------------Start of consistency algorithms. Replaced by Didier and Berence---
        externaloutliers_df = pd.DataFrame()
        def externalConsistency(seriesData):
            series = pd.to_numeric(seriesData, errors='coerce').dropna().unique()
            if len(series)==2:
                v1 = pd.to_numeric(series[0])
                v2 = pd.to_numeric(series[1])
                rateOfChange = 0
                if (min(v1,v2)):
                    rateOfChange = np.abs((v1-v2)/min(v1,v2))
                if (rateOfChange > 0.5):
                    return [max(v1, v2)]
                else:
                    return None
            if (len(series) > 2):
                MedianVal = np.median(series)
                madValue = smr.mad(series)
                seriesFinal = np.abs((series - MedianVal)/madValue)
                if(len(series[seriesFinal>3].tolist())):
                    return series[seriesFinal>3].tolist()
                else:
                    return None

        aggDataExtInc = data.groupby(
            ['Country', 'Indicator Name','Year', 'CategoryOption'], 
            as_index=False).agg({'Value':externalConsistency})

        aggDataExtInc = aggDataExtInc[aggDataExtInc.Value.notnull()]
        s = aggDataExtInc.apply(lambda x: pd.Series(
            x['Value']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'Value'
        aggDataExtInc = aggDataExtInc.drop('Value', axis=1).join(s)

        dataExtInc = data.copy()
        keys = list(aggDataExtInc.columns.values)
        dataExtInc['Value'] = pd.to_numeric(dataExtInc['Value'], errors='coerce')
        dataExtInc = dataExtInc[dataExtInc.Value.notnull()]

        i1 = dataExtInc.set_index(keys).index
        i2 = aggDataExtInc.set_index(keys).index

        
        ExOutliersExtCons = dataExtInc[i1.isin(i2)].copy()
        ExOutliersExtCons['Check_External_Inconsistency'] = \
            'This value seems to be an outlier for an external consistency'
        externaloutliers_df = ExOutliersExtCons.copy()        

        if not externaloutliers_df.empty: # check whether the dataframe is empty
            external_outliers_df=externaloutliers_df.rename(
                {'Indicator Name':'indicator_name','Country':'location',
                'CategoryOption':'categoryoption','DataSource':'datasource',
                'measure type':'measure_type','Value':'value','Year':'period',
                'Check_External_Inconsistency':'external_consistency'},
                axis=1)  

            extraconsistency_checker = external_outliers_df.to_records(index=True)
            try:    
                extraconsistencies = [           
                    DqaExternalConsistencyOutliersRemarks(
                        indicator_name=record['indicator_name'],
                        location=record['location'],
                        categoryoption=record['categoryoption'],
                        datasource=record['datasource'],
                        measure_type=record['measure_type'],
                        value=record['value'],
                        period=record['period'],
                        external_consistency=record['external_consistency'],                   
                        user = current_user    
                    )
                    for record in extraconsistency_checker
                ]
                records = DqaExternalConsistencyOutliersRemarks.objects.bulk_create(
                    extraconsistencies,ignore_conflicts=True,)
            except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                pass 
            except: # ignore othe database related errors
                print('Unknown Error has occured')               
    

        # Internal consistency : By Indicator per categoryoption (Considering all data sources )
        internaloutliers_df = pd.DataFrame()
        def internalConsistency(seriesData):
            series = pd.to_numeric(seriesData, errors='coerce').dropna().unique()
            if len(series)==2:
                v1 = pd.to_numeric(series[0])
                v2 = pd.to_numeric(series[1])
                rateOfChange = 0
                if (min(v1,v2)):
                    rateOfChange = np.abs((v1-v2)/min(v1,v2))
                if (rateOfChange > 0.5):
                    return [max(v1, v2)]
                else:
                    return None
            if ((len(series) > 2) & (len(series) < 10)):
                MedianVal = np.median(series)
                madValue = smr.mad(series)
                seriesFinal = np.abs((series - MedianVal) / madValue)
                if(len(series[seriesFinal>3].tolist())):
                    return series[seriesFinal>3].tolist()
                else:
                    return None
            if len(series)>= 10:
                MedianVal = np.median(series)
                series1 = series[series <= MedianVal]
                MedianVal1 = np.median(series1)
                madValue1 = smr.mad(series1)
                seriesFinal1 = np.abs((series1 - MedianVal1) / madValue1)
                ssf1 = series1[seriesFinal1 > 3].tolist()
                series2 = series[series > MedianVal]
                MedianVal2 = np.median(series2)
                madValue2 = smr.mad(series2)
                seriesFinal2 = np.abs((series2 - MedianVal2) / madValue2)
                ssf2 = series2[seriesFinal2 > 3].tolist()
                seriesFinal = ssf1 + ssf2
                if(len(seriesFinal)):
                    return seriesFinal
                else:
                    return None

        aggDataIntInc = data.groupby(['Country', 'Indicator Name', 
                                'DataSource', 'CategoryOption'], as_index=False).agg(
                                    {'Value':internalConsistency})
        aggDataIntInc = aggDataIntInc[aggDataIntInc.Value.notnull()]
        s = aggDataIntInc.apply(lambda x: pd.Series(
            x['Value']), axis=1).stack().reset_index(level=1, drop=True)
        s.name = 'Value'
        aggDataIntInc = aggDataIntInc.drop('Value', axis=1).join(s)

        dataIntInc = data.copy()
        keys = list(aggDataIntInc.columns.values)
        dataIntInc['Value'] = pd.to_numeric(dataIntInc['Value'], errors='coerce')
        dataIntInc = dataIntInc[dataIntInc.Value.notnull()]
        i1 = dataIntInc.set_index(keys).index
        i2 = aggDataIntInc.set_index(keys).index

        InternalConsistency = dataIntInc[i1.isin(i2)].copy()

        InternalConsistency['Check_Internal_Inconsistency'] = \
            'This value seems to be an outlier for an internal consistency'
        internaloutliers_df = InternalConsistency.copy()

        if not internaloutliers_df.empty: # check whether the dataframe is empty
            internal_outliers_df=internaloutliers_df.rename(
                {'Indicator Name':'indicator_name','Country':'location',
                'CategoryOption':'categoryoption','DataSource':'datasource',
                'measure type':'measure_type','Value':'value','Year':'period',
                'Check_Internal_Inconsistency':'internal_consistency'},axis=1)  
        
            intraconsistency_checker = internal_outliers_df.to_records(index=True)
            try:    
                intraconsistencies = [           
                    DqaInternalConsistencyOutliersRemarks(
                        indicator_name=record['indicator_name'],
                        location=record['location'],
                        categoryoption=record['categoryoption'],
                        datasource=record['datasource'],
                        measure_type=record['measure_type'],
                        value=record['value'],
                        period=record['period'],
                        internal_consistency=record['internal_consistency'],                   
                        user = current_user    
                    )
                    for record in intraconsistency_checker
                ]
                records = DqaInternalConsistencyOutliersRemarks.objects.bulk_create(
                    intraconsistencies,ignore_conflicts=True,)
            except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                pass 
            except: # ignore othe database related errors
                print('Unknown Error has occured') 

        # import pdb; pdb.set_trace()
        # --------------End of consistency inspection algorithms. To be replace with corrected from Didier and Berence---


        # -----------Miscellaneous algorithm for checking Consistancies per mesure type: Count(numeric Integer) ---------- 
        # Checking consistancies per mesure type: Not numeric Value
        dataCountNumeric = data.loc[data['measure type'] == 'Count (Numeric Integer)']
        dataCountMT = dataCountNumeric.copy() # create a copy of the dataframe
        dataCountMT['Value'] = pd.to_numeric(dataCountMT['Value'], errors='coerce')

        CountOverAllChecking = dataCountMT.loc[dataCountMT['Value'].isna()]
        if not CountOverAllChecking.empty: # check whether the dataframe is empty
            CountOverAllChecking.loc[:,'Check_value'] = \
                'This value does not suit with its mesure type'
            integervalue_df = CountOverAllChecking # Didier's data7 Total alcohol per capita (age 15+ years) consu... WHO / GHO  NaN

            # Return values with not null floating point
            dataCountMT_WNNFP = dataCountMT[dataCountMT['Value'].apply(
                lambda x: x % 1 )>0.001]
            dataCountMT_WNNFP.loc[:,'Check_value'] = \
                'This mesure type does not allow floating point'
            floatvalue_df = dataCountMT_WNNFP #Didier's data8 
                    
            combinedvalue_checker = pd.concat([integervalue_df,floatvalue_df],axis=0) # append rows (axis=0)
            combinedvalue_checker.rename({'Indicator Name':'indicator_name',
                'Country':'location','CategoryOption':'categoryoption',
                'DataSource':'datasource','measure type':'measure_type',
                'Value':'value','Year':'period','Check_value':'check_value'},
                axis=1, inplace=True) 

            valuetypes_checker = combinedvalue_checker.to_records(index=True)
            try:    
                valuetypes = [           
                    DqaValueTypesConsistencyRemarks(
                        indicator_name=record['indicator_name'],
                        location=record['location'],
                        categoryoption=record['categoryoption'],
                        datasource=record['datasource'],
                        measure_type=record['measure_type'],
                        value=record['value'],
                        period=record['period'],
                        check_value=record['check_value'],                    
                        user = current_user    
                    )
                    for record in valuetypes_checker
                ]
                records = DqaValueTypesConsistencyRemarks.objects.bulk_create(
                    valuetypes,ignore_conflicts=True,)             
            except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                pass 
            except: # ignore othe database related errors
                print('Unknown Error has occured') 
    
    else: # if no data has been loaded into the dataframe view return no data message
        print('Sorry. No data has been loaded') 
 

    # -------End of data validation algorithms derived from Didier's pandas code---------------------------------
    if not data.empty:
        success = "Data validation reports created and saved into the database"
    else:
        success ="Sorry. The Facts dataframe has no dataset to be  validated"     
    context = {              
        'success':success,
    }
    return render(request,'data_quality/home.html',context)