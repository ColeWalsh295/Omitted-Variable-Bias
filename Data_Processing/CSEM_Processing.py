import os
import pandas as pd
from datetime import datetime
from glob import glob

# dictionary of correct answers taken from PhysPort
correct_ans = pd.Series({'Q1':2, 'Q2':1, 'Q3':2, 'Q4':2, 'Q5':3, 'Q6':5, 'Q7':2, 'Q8':2, 'Q9':2, 'Q10':3, 'Q11':5, 'Q12':4,
                         'Q13':5, 'Q14':4, 'Q15':1, 'Q16':5, 'Q17':5, 'Q18':4, 'Q19':1, 'Q20':4, 'Q21':5, 'Q22':4, 'Q23':1,
                         'Q24':3, 'Q25':4, 'Q26':1, 'Q27':5, 'Q28':3, 'Q29':3, 'Q30':1, 'Q31':5, 'Q32':4})

# Natasha Holmes compiled an excel file of students that opted out of research...we need to remove those students from our dataset
Consent_df = pd.read_excel('C:/Users/Cole/Documents/DATA/MasterList.xlsx')
Consent_df['FullName'] = (Consent_df['First Name:'] + Consent_df['Last Name:']).str.lower().str.replace(' ', '')
Consent_df['Course'] = Consent_df['Course'].str.split(' ').str.get(1).apply(lambda x: 'P' + x[:-1]) # some courses were logged as Phys xxxx, others just as xxxx

def Clean_CSEM(file, time_cutoff = None):
    """Filter and score CSEM file

    Keyword arguments:
    file -- file path for raw CSEM csv file
    time_cutoff -- time to completion used to filter out responses in seconds
    """
    # ADD REMOVE NON-CONSENTING STUDENTS

    df = pd.read_csv(file, skiprows = [1]) # first line after header is descriptive text

    if(time_cutoff is not None):
        df[['V3', 'V4']] = df[['V3', 'V4']].apply(pd.to_datetime) # V3 and V4 are the start and end timetsamps, respectively
        df['Time'] = (df['V4'] - df['V3']).dt.seconds
        df = df.loc[df['Time'] >= time_cutoff, :] # filter out surveys that took less than a certain time

    df['Name'] = df['Name'].str.lower().str.replace(' ', '')
    df['Q38'] = df['Q38'].str.lower().str.replace(' ', '') # poorly formatted file, Q38 is actually first name
    df['NetID'] = df['NetID'].astype(str).apply(lambda x: x.split('@')[0].lower()).str.replace(' ', '')
    df['Q39'] = df['Q39'].astype(str).str.lower().str.replace(' ', '') # Q39 is student ID

    df = df.drop_duplicates(subset = ['Name', 'Q38'],
                            keep = 'last').drop_duplicates(subset = ['NetID'],
                                                           keep = 'last').drop_duplicates(subset = ['Q39'], keep = 'last')

    df['Course'] = df['Course'].map({1:'P1102', 2:'P2208', 3:'P2213', 4:'P2217'})
    df['FullName'] = (df['Q38'] + df['Name']).str.lower().str.replace(' ', '')

    df = pd.merge(df, Consent_df[['Course', 'FullName']], on = ['Course', 'FullName'], how = 'left', indicator = 'OptOut?')
    df = df.loc[df['OptOut?'] == 'left_only', :].drop(columns = ['OptOut?', 'FullName'])

    df[correct_ans.index] = 1 * (df[correct_ans.index] == correct_ans)
    df['Total_Score'] = df[correct_ans.index].sum(axis = 1)

    return df

def Match_CSEM(pre_file, post_file, Semester, Year, raw = True, time_cutoff = None):
    """Outer join pre and posttest CSEM files together

    Keyword arguments:
    pre_file -- file path to raw CSEM pretest csv file
    post_file -- file path to raw CSEM posttest csv file
    Semester -- semester that the survey was adminsitered; either Fall, Spring, or Summer
    Year -- year that the survey was administered
    raw -- binary, whether the input files are raw or have been previously scored
    time_cutoff -- time cutoff to use when filtering surveys, passed to Clean_CSEM
    """

    if raw:
        df_pre = Clean_CSEM(pre_file, time_cutoff = time_cutoff)
        df_post = Clean_CSEM(post_file, time_cutoff = time_cutoff)

    # merge separately on full name, netID, and ID to capture as many students as possible that took both pre and posttests
    df_name = pd.merge(df_pre, df_post, how = 'inner', on = ['Name', 'Q38'])
    df_netID = pd.merge(df_pre, df_post, how = 'inner', on = 'NetID')
    df_studentID = pd.merge(df_pre, df_post, how = 'inner', on = 'Q39')

    # we make sure students aren't double counted
    df_in = pd.concat([df_name, df_netID, df_studentID], axis = 0, join = 'outer').reset_index(drop = True).drop_duplicates(subset = ['V1_x']).drop_duplicates(subset = ['V1_y'])

    # and put back students who only took one of the pre or posttest in our dataset
    Pre_Cols = [col if col in df_in.columns else col + '_x' for col in df_pre.columns]
    Out_Pre = df_pre.loc[~df_pre['V1'].isin(df_in['V1_x'])]
    Out_Pre.columns = Pre_Cols

    Post_Cols = [col if col in df_in.columns else col + '_y' for col in df_post.columns]
    Out_Post = df_post.loc[~df_post['V1'].isin(df_in['V1_y'])]
    Out_Post.columns = Post_Cols

    df = pd.concat([df_in, Out_Pre, Out_Post], axis = 0, join = 'outer').reset_index(drop = True)

    df['NetID'] = df['NetID'].fillna(df['NetID_y']).fillna(df['NetID_x'])
    df['Q39'] = df['Q39'].fillna(df['Q39_y']).fillna(df['Q39_x'])
    df['Course'] = df['Course_y'].fillna(df['Course_x'])
    df = df.drop(columns = ['NetID_x', 'NetID_y', 'Q39_x', 'Q39_y', 'Q38_x', 'Q38_y', 'Name_x', 'Name_y', 'Course_x', 'Course_y'])

    df['Semester'] = Semester
    df['Year'] = Year

    return df

def BuildMasterCSEMDataset(dir, time_cutoff = None):
    """Construct master CSEM dataset of matched and unmatched surveys

    Keyword arguments:
    dir -- directory where CSEM raw files are stored
    time_cutoff -- time cutoff to use when filtering surveys, passed to Clean_CSEM
    """

    os.chdir(dir)
    pre_files = glob('RAW/**/*Pre*csv', recursive = True)
    post_files = glob('RAW/**/*Post*csv', recursive = True)

    # semester and year is in the filename, we'll just concatenate those together
    matched_dfs = [Match_CSEM(pre_f, post_files[i], pre_f.split('_')[3][:2].upper(), pre_f.split('_')[4].split('.')[0], time_cutoff = time_cutoff) for i, pre_f in enumerate(pre_files)]
    df = pd.concat(matched_dfs, axis = 0)

    df.to_csv('CSEM_Master.csv', index = False)
    return df
