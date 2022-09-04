from django.shortcuts import render
from django_pandas.io import *
from django.db import IntegrityError


import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz,process
from functools import reduce

from sqlalchemy import create_engine #helper for saving dataframes to db
import MySQLdb # drivers for accessing the database through sqlalchemy

from indicators.models import FactDataIndicator
from aho_datacapturetool import settings

import json

from .models import (Facts_DataFrame,CategoryOptions_Validator,MeasureTypes_Validator,
    DataSource_Validator,Mutiple_MeasureTypes,DqaInvalidDatasourceRemarks,
    DqaInvalidCategoryoptionRemarks,DqaInvalidMeasuretypeRemarks,Similarity_Index,
    DqaInvalidPeriodRemarks,DqaExternalConsistencyOutliersRemarks,
    DqaInternalConsistencyOutliersRemarks,DqaValueTypesConsistencyRemarks
    )

def db_connection():
    user = settings.DQUSER
    pw =settings.DQPASS
    db = settings.DQDB
    host = settings.DQHOST
    # engine = create_engine("mysql+mysqldb://{user}:{pw}@{host}/{db}"
    #                 .format(user=user,pw=pw,host=host,db=db))

    engine = create_engine("mysql+mysqldb://{user}:{pw}@{host}/{db}"
                .format(user=user,pw=pw,host=host,db=db),
                connect_args={
                        "ssl": {
                            "ssl_ca": "/home/site/cert/BaltimoreCyberTrustRoot.crt.pem",
                        }
                    }
            )

    return engine

    

def check_data_quality(request):
    con= db_connection() # create connection to database using sqlalchemy engine

    facts_df = pd.DataFrame() # initialize the facts dataframe with a null value
    data = pd.DataFrame()
    groups = list(request.user.groups.values_list('user', flat=True))
    user = request.user.id  
    location = request.user.location.name
    language = request.LANGUAGE_CODE 
    
    
    # -----------------------------------Start Save Data Validation DataFrames---------------------------------------------------------
    # Create data source dataframe and save it into the database into measure types model 
    try:
        MesureTypeValid = pd.read_csv('Datasets/Mesuretype.csv', encoding='iso-8859-1')
        
        MesureTypeValid.rename({'IndicatorId':'afrocode','Indicator Name':'indicator_name', 
                'measurementmethod':'measure_type','measuremethod_id':'measuremethod_id'},
                axis=1, inplace=True)    
        measuretypes = json.loads(MesureTypeValid.to_json(
            orient='records', index=True))  # converts json to dict
        # Use try..except block to loop through and save measure objects into the database
        try:
            for record in measuretypes:    
                measuretype = MeasureTypes_Validator.objects.update_or_create(
                    afrocode=record['afrocode'],
                    indicator_name=record['indicator_name'],
                    measure_type=record['measure_type'],
                    measuremethod_id=record['measuremethod_id'],
                )
        except:
            pass
    except:
        pass


    # # Create data source dataframe and save it into the database into the datasource model
    try:
        DataSourceValid = pd.read_csv('Datasets/Datasource.csv', encoding='iso-8859-1')  
        DataSourceValid.rename(
            {'IndicatorId':'afrocode','Indicator Name':'indicator_name', 
                'DataSource':'datasource','DatasourceId':'datasource_id'},
                axis=1, inplace=True)   
        datasources = json.loads(DataSourceValid.to_json(
            orient='records', index=True))  # converts json to dict

        # use try..except block to loop through and save measure objects into the database
        try:
            for record in datasources:
                datasource = DataSource_Validator.objects.update_or_create(
                    afrocode=record['afrocode'],
                    indicator_name=record['indicator_name'],
                    datasource=record['datasource'],
                    datasource_id=record['datasource_id'],
                )
        except:
            pass
    except:
        pass   
    
    # Create data source dataframe and save it into the database into the datasource model
    try:
        CategoryOptionValid = pd.read_csv('Datasets/Categoryoption.csv', encoding='iso-8859-1')
        CategoryOptionValid.rename({'IndicatorId':'afrocode','Indicator Name':'indicator_name', 
                'DataSource':'datasource','DatasourceId':'datasource_id','Category':'categoryoption',
                'CategoryId':'categoryoption_id'},axis=1, inplace=True)   

        categoryoptions = json.loads(CategoryOptionValid.to_json(
            orient='records', index=True))  # convert to records
        try:    
            for record in categoryoptions:
                categoryoption = CategoryOptions_Validator.objects.update_or_create(
                    afrocode=record['afrocode'],
                    indicator_name=record['indicator_name'],
                    categoryoption=record['categoryoption'],
                    categoryoption_id=record['categoryoption_id'],
                )
        except:
            pass
    except:
        pass
    # ----------------------------------End Data Validation DataFrames---------------------------------------------------------

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
            'location':'Country','categoryoption':'CategoryOption','datasource':'DataSource',
            'measure_type':'measure type','value':'Value','period':'Year'},axis=1)

        # -----------------------------------Misscellanious algorithm - Count Data Source and measure Type For Each Indicators-----
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
                'Check_Mesure_Type':'remarks'},axis=1)       
       
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
                multi_source_measures_df = data[data.Check_Mesure_Type.str.len() > 0] # Didier's data2

                multi_source_measures_df=multi_source_measures_df.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Year':'period','Value':'value',
                    'Year':'period','Check_Mesure_Type':'remarks'},axis=1)    
                
                # Concatenate the two frames using columns (axis=1) and save on the database
                measures_checker_df = pd.concat((multi_measures_df, multi_source_measures_df), axis = 1)
                measures_checker_df.loc[:,'user_id'] = request.user.id # add logged user id column
                if con: #store similarity scores into similarities table
                    try:
                        measures_checker_df.index = range(1,len(measures_checker_df)+1) #set index to start from 1 instead of default 0
                        measures_checker_df.to_sql(
                            'dqa_multiple_indicators_checker', con = con, 
                            if_exists = 'append',index=True,index_label='id',chunksize = 1000) # set index as true to save as id 
                    except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                        pass
                    except:
                        print('Unknown Error has occured')   
         

    # -------------------------------Import algorithm 1 - indicators with wrong measure types--------------------------
        valid_datasources_qs = DataSource_Validator.objects.all().order_by('afrocode')
        data.drop('Check_Mesure_Type', axis=1, inplace=True) # remove period remarks from the facts dataframe     
        bad_datasource = pd.DataFrame()
        if len(qs) >0:
            DataSourceValid = valid_datasources_qs.to_dataframe(['id', 'afrocode', 'indicator_name',
                'datasource','datasource_id'],index='id')
            DataSourceValid.rename({'indicator_name':'Indicator Name',
                'datasource':'DataSource'},axis=1, inplace=True)
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
            dataWDS.loc[:,'Check_Data_Source'] = 'This data source is not applicable to this indicator'
            bad_datasource = dataWDS # Didier's data3: create dataframe for wrong data sources
            
            if not bad_datasource.empty: # use a.empty instead of boolean to check whether df is empty
                bad_datasource_df=bad_datasource.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Value':'value','Year':'period',
                    'Check_Data_Source':'check_data_source'},axis=1)  
               
                if con: #store similarity scores into similarities table
                    try:
                        bad_datasource_df.loc[:,'user_id'] = request.user.id # add logged user id column
                        bad_datasource_df.index = range(1,len(bad_datasource_df)+1) #set index to start from 1 instead of default 0
                        bad_datasource_df.to_sql(
                            'dqa_invalid_datasource_remarks', con = con, 
                            if_exists = 'append',index=True,index_label='id',chunksize = 1000) # set index as true to save as id 
                    except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                        pass
                    except:
                        print('Unknown Error has occured')   
            # import pdb; pdb.set_trace() # checkpoint

        # -------------------------------Import algorithm 2 - indicators with wrong category options--------------------------
        valid_categoryoptions_qs = CategoryOptions_Validator.objects.all().order_by('afrocode')
        categoryoption_df = pd.DataFrame()
        measuretypes_df = pd.DataFrame()
        if len(qs) >0:
            CategoryOptionValid = valid_categoryoptions_qs.to_dataframe(['id', 'afrocode', 'indicator_name',
                'categoryoption','categoryoption_id'],index='id')
            CategoryOptionValid.rename({'indicator_name':'Indicator Name','categoryoption':'Category'},
                axis=1, inplace=True)
            UniqueIndicatorV = DataSourceValid['Indicator Name'].unique().tolist()
            
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
                        dataWCO.loc[:,'Check_Category_Option'] = 'This category option is not applicable to this indicator'            
            categoryoption_df = dataWCO # Didier's data4: Create dataframe with check measure type remarks column
        
            if not categoryoption_df.empty: # check whether the dataframe is empty
                bad_categoryoption_df=categoryoption_df.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Value':'value','Year':'period',
                    'Check_Category_Option':'check_category_option'},axis=1)  

                if con: #store similarity scores into similarities table
                    try:
                        bad_categoryoption_df.loc[:,'user_id'] = request.user.id # add logged user id column
                        bad_categoryoption_df.index = range(1,len(bad_categoryoption_df)+1) #set index to start from 1 instead of default 0
                        bad_categoryoption_df.to_sql(
                            'dqa_invalid_categoryoption_remarks', con = con, 
                            if_exists = 'append',index=True,index_label='id',chunksize = 1000)   
                    except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                        pass
                    except:
                        print('Unknown Error has occured')  
                

        # -------------------------------Import algorithm 3 - indicators with wrong measure types--------------------------
        valid_measures_qs = MeasureTypes_Validator.objects.all().order_by('afrocode')
        if len(qs) >0:
            MesureTypeValid = valid_measures_qs.to_dataframe(['id', 'afrocode', 'indicator_name',
                'measure_type','measuremethod_id'],index='id')
            MesureTypeValid.rename({'indicator_name':'Indicator Name',
            'measure_type':'measure type'},axis=1, inplace=True)

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
                        dataWMT.loc[:,'Check_Mesure_Type'] = 'This mesure type is not applicable to this indicator'
            measuretypes_df = dataWMT # Didier's data5 Create dataframe with check measure type remarks column
            
            if not measuretypes_df.empty: # check whether the dataframe is empty
                bad_measuretype_df=measuretypes_df.rename(
                    {'Indicator Name':'indicator_name','Country':'location',
                    'CategoryOption':'categoryoption','DataSource':'datasource',
                    'measure type':'measure_type','Value':'value','Year':'period',
                    'Check_Mesure_Type':'check_mesure_type'},axis=1)  


                if con: #store similarity scores into similarities table
                    try:
                        bad_measuretype_df.loc[:,'user_id'] = request.user.id # add logged user id column
                        bad_measuretype_df.index = range(1,len(bad_measuretype_df)+1) #set index to start from 1 instead of default 0
                        bad_measuretype_df.to_sql(
                            'dqa_invalid_measuretype_remarks', con = con, 
                            if_exists = 'append',index=True,index_label='id',chunksize = 1000)   
                    except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                        pass
                    except:
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


        if con: #store similarity scores into similarities table
            try:
                Check_similarities.loc[:,'user_id'] = request.user.id # add logged user id column
                Check_similarities.index = range(1,len(Check_similarities)+1) #set index to start from 1 instead of default 0
                Check_similarities.to_sql(
                    'dqa_similar_indicators_score', con = con, 
                    if_exists = 'append',index=True,index_label='id',chunksize = 1000)   
            except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                pass
            except:
                print('Unknown Error has occured')  
   

        # -------------------------------------End of comparing indicators for similarity score----------------------------             

        # -------------------------------Start of miscellanious algorithms - Year verification -----------------------------------
        MultipleYearTypeIndicator = pd.DataFrame()
        dataWithSelectedColumns = data[['Country', 'Indicator Name', 'DataSource', 'Year']]
        dataWithSelectedColumns['CYear'] = dataWithSelectedColumns['Year'].apply(len) #count characters in year string

        NumberYearTypeIndicator = dataWithSelectedColumns.groupby(
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
            if con: #store similarity scores into similarities table
                try:
                    bad_periods_df.loc[:,'user_id'] = request.user.id # add logged user id column
                    bad_periods_df.index = range(1,len(bad_periods_df)+1) #set index to start from 1 instead of default 0
                    bad_periods_df.to_sql('dqa_invalid_period_remarks', con = con, 
                        if_exists = 'append',index=True,index_label='id',chunksize = 1000)   
                except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                    pass
                except:
                    print('Unknown Error has occured') 


        # --------------Start of consistency inpection algorithms. To be replace with corrected from Didier and Berence---
        dataCountMT = data[data['measure type'] == 'Count (Numeric Integer)']
        dataCountMT['Value'] = pd.to_numeric(dataCountMT['Value'], errors='coerce')
        
        CountriesCMT = dataCountMT['Country'].unique().tolist()
        ExOutliersCMT = pd.DataFrame(columns=dataCountMT.columns.tolist())
        externaloutliers_df = pd.DataFrame()
   
        for country in CountriesCMT:
            dataC = dataCountMT[dataCountMT['Country'] == country]
            CIndicatorsCMT = dataC['Indicator Name'].unique().tolist()
            for indicator in CIndicatorsCMT:
                CdataR = dataC[dataC['Indicator Name'] == indicator]
                CatOptCMT = CdataR['CategoryOption'].unique().tolist()
                for catopt in CatOptCMT:
                    dataCOpt = CdataR[CdataR['CategoryOption'] == catopt]
                    MeanVal = np.mean(dataCOpt['Value'])
                    SDVal = np.std(dataCOpt['Value']) 
                    dataCOpt = dataCOpt[( # replaced append() with concat() function due to depricated append
                        dataCOpt.Value > MeanVal + 3*SDVal) | (dataCOpt.Value < MeanVal - 3*SDVal)]
                    if len(dataCOpt)!=0: #improved Didier's algorithm to check for empty list
                        ExOutliersCMT =  pd.concat((
                            ExOutliersCMT,dataCOpt),axis = 0,ignore_index = True)
                        ExOutliersCMT.loc[:,'Check_value'] = 'External consistency violation: \
                            This value seems to be an outlier'
        externaloutliers_df = ExOutliersCMT #Didier's data9

        if not externaloutliers_df.empty: # check whether the dataframe is empty
            external_outliers_df=externaloutliers_df.rename(
                {'Indicator Name':'indicator_name','Country':'location','CategoryOption':'categoryoption',
                'DataSource':'datasource','measure type':'measure_type','Value':'value','Year':'period',
                'Check_value':'external_consistency'},
            axis=1)  

            if con: #store external outliers
                try:
                    external_outliers_df.loc[:,'user_id'] = request.user.id # add logged user id column
                    external_outliers_df.index = range(1,len(external_outliers_df)+1) #set index to start from 1 instead of default 0
                    external_outliers_df.to_sql('dqa_external_inconsistencies_remarks', con = con, 
                        if_exists = 'append',index=True,index_label='id',chunksize = 1000)   
                except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                    pass
                except:
                    print('Unknown Error has occured')  

 
        # Internal consistency : By Indicator per categoryoption (Considering all data sources )
        CountriesCMT = dataCountMT['Country'].unique().tolist()
        InOutliersCMT = pd.DataFrame(columns=dataCountMT.columns.tolist())
        
        internaloutliers_df = pd.DataFrame()
        for country in CountriesCMT:
            dataC = dataCountMT[dataCountMT['Country'] == country]
            CIndicatorsCMT = dataC['Indicator Name'].unique().tolist()
            for indicator in CIndicatorsCMT:
                CdataR = dataC[dataC['Indicator Name'] == indicator]
                CatOptCMT = CdataR['CategoryOption'].unique().tolist()
                for catopt in CatOptCMT:
                    dataCOpt = CdataR[CdataR['CategoryOption'] == catopt]
                    dataSourceCMT = dataCOpt['DataSource'].unique().tolist()
                    for ds in dataSourceCMT:
                        dataDS = dataCOpt[dataCOpt['DataSource'] == ds]
                        MeanVal = np.mean(dataDS['Value'])
                        SDVal = np.std(dataDS['Value'])   
                        dataDS = dataDS[( # replaced append() with concat()
                            dataDS.Value > MeanVal + 3*SDVal) | (dataDS.Value < MeanVal - 3*SDVal)]
                        if len(dataDS)!=0: #improved Didier's algorithm to check for empty list
                            InOutliersCMT =  pd.concat((InOutliersCMT,dataDS),axis = 0,ignore_index = True)
                            InOutliersCMT.loc[:,'Check_value'] = 'Internal consistency violation: \
                                This value seems to be an outlier'
        internaloutliers_df = InOutliersCMT #Didier's data10

        if not internaloutliers_df.empty: # check whether the dataframe is empty
            internal_outliers_df=internaloutliers_df.rename(
                {'Indicator Name':'indicator_name','Country':'location',
                'CategoryOption':'categoryoption','DataSource':'datasource',
                'measure type':'measure_type','Value':'value','Year':'period',
                'Check_value':'internal_consistency'},axis=1)  

            if con: #store external outliers
                try:
                    internal_outliers_df.loc[:,'user_id'] = request.user.id # add logged user id column
                    internal_outliers_df.index = range(1,len(internal_outliers_df)+1) #set index to start from 1 instead of default 0
                    internal_outliers_df.to_sql('dqa_internal_consistencies_remarks', con = con, 
                        if_exists = 'append',index=True,index_label='id',chunksize = 1000)   
                except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                    pass
                except:
                    print('Unknown Error has occured')  
  
        # --------------End of consistency inspection algorithms. To be replace with corrected from Didier and Berence---


        # -----------Miscellaneous algorithm for checking Consistancies per mesure type: Count(numeric Integer) ---------- 
        # Checking consistancies per mesure type: Not numeric Value
        CountOverAllChecking = dataCountMT[dataCountMT['Value'].isna()]
        
        if not CountOverAllChecking.empty: # check whether the dataframe is empty
            CountOverAllChecking.loc[:,'Check_value'] = 'This value does not suit with its mesure type'
            integervalue_df = CountOverAllChecking # Didier's data7 Total alcohol per capita (age 15+ years) consu... WHO / GHO  NaN

            # Return values with not null floating point
            dataCountMT_WNNFP = dataCountMT[dataCountMT['Value'].apply(lambda x: x % 1 )>0.001]
            dataCountMT_WNNFP.loc[:,'Check_value'] = 'This mesure type does not allow floating point'
            floatvalue_df = dataCountMT_WNNFP #Didier's data8 
                    
            combinedvalue_checker = pd.concat([integervalue_df,floatvalue_df],axis=0) # append rows (axis=0)
            combinedvalue_checker.rename({'Indicator Name':'indicator_name',
                'Country':'location','CategoryOption':'categoryoption',
                'DataSource':'datasource','measure type':'measure_type',
                'Value':'value','Year':'period','Check_value':'check_value'},
                axis=1, inplace=True) 

            if con: #store combined value_checker outliers
                try:
                    combinedvalue_checker.loc[:,'user_id'] = request.user.id # add logged user id column
                    combinedvalue_checker.index = range(1,len(combinedvalue_checker)+1) #set index to start from 1 instead of default 0
                    combinedvalue_checker.to_sql('dqa_valuetype_consistencies_remarks', con = con, 
                        if_exists = 'append',index=True,index_label='id',chunksize = 1000)   
                except(MySQLdb.IntegrityError, MySQLdb.OperationalError) as e:
                    pass
                except:
                    print('Unknown Error has occured') 


    else: 
        print('No data') 
        
# -----------------End of data validation algorithms derived from Didier's pandas code---------------------------------
    if not data.empty:
        success = "Data validation reports created and saved into the Database"
    else:
        success ="Sorry. The facts table has no datasets to be  validated"     
    context = {              
        'success':success,
    }
    return render(request,'data_quality/home.html',context)