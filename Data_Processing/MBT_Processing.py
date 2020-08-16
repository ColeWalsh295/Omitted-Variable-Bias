import os
import pandas as pd
from datetime import datetime
from glob import glob

Correct_Answers = {'Q1':2, 'Q2':4, 'Q3':5, 'Q4':3, 'Q5':1, 'Q6':3, 'Q7':3, 'Q8':4, 'Q9':1, 'Q10':5, 'Q11':5, 'Q12':3,
                   'Q13':2, 'Q14':2, 'Q15':5, 'Q16':1, 'Q17':4, 'Q18':2, 'Q19':3, 'Q20':3, 'Q21':1, 'Q22':2,
                   'Q23':4, 'Q24':1, 'Q25':1, 'Q26':5}

# Natasha Holmes compiled an excel file of students that opted out of research...we need to remove those students from our dataset
Consent_df = pd.read_excel('C:/Users/Cole/Documents/DATA/MasterList.xlsx')
Consent_df['FullName'] = (Consent_df['First Name:'] + Consent_df['Last Name:']).str.lower().str.replace(' ', '')
Consent_df['Course'] = Consent_df['Course'].str.split(' ').str.get(1).apply(lambda x: 'P' + x[:-1]) # some courses were logged as Phys xxxx, others just as xxxx


def Clean_MBT(File, time_cutoff):
    """Filter and score CSEM file

    Keyword arguments:
    File -- file path for raw MBT csv file
    time_cutoff -- time to completion used to filter out responses in seconds
    """

    df = pd.read_csv(File, skiprows = [1])
    if (df.dtypes['Q1'] != 'float64'):
        df = pd.read_csv(File, skiprows = [1, 2]) # some files have two header rows and different column names
        df = df.rename(columns = {'ResponseId':'V1', 'Duration (in seconds)':'Duration'})
    else:
        df[['V3', 'V4']] = df[['V3', 'V4']].apply(pd.to_datetime) # V3 and V4 are the start and end timetsamps, respectively
        df['Duration'] = (df['V4'] - df['V3']).dt.seconds
    if time_cutoff is not None:
        df = df.loc[df['Duration'] >= time_cutoff, :] # filter out surveys that took less than a certain time

    if('Q47' in df.columns): # some of the courses used different column names and had an extra column distinguishing between courses
        df['Course'] = df['Q47'].map({2:'P1112', 3:'P1116'})
        df = df.rename(columns = {'Q49':'QA', 'Q51':'QB', 'Q53':'QC', 'Q61':'QD'})
    else:
        df['Course'] = 'P1112'

    df[['QA', 'QB', 'QC', 'QD']] = df[['QA', 'QB', 'QC', 'QD']].apply(lambda x: x.astype(str).str.lower()) # ID columns
    df = df.drop_duplicates(subset = ['QA', 'QB']).drop_duplicates(subset = ['QC']).drop_duplicates(subset = ['QD'])

    df['FullName'] = (df['QA'] + df['QB']).str.lower().str.replace(' ', '')
    df = pd.merge(df, Consent_df[['Course', 'FullName']], on = ['Course', 'FullName'], how = 'left', indicator = 'OptOut?')
    df = df.loc[df['OptOut?'] == 'left_only', :].drop(columns = ['OptOut?', 'FullName'])

    for question, answer in Correct_Answers.items():
        df[question + '_Score'] = 1 * (df[question] == answer)
    df['Total_Score'] = df.loc[:, [col for col in df.columns if 'Score' in col]].sum(axis = 1)

    return df

def Match_MBT(pre_file, post_file, Semester, Year, raw = True, time_cutoff = None):
    """Outer join pre and posttest MBT files together

    Keyword arguments:
    pre_file -- file path to raw MBT pretest csv file
    post_file -- file path to raw MBT posttest csv file
    Semester -- semester that the survey was adminsitered; either Fall, Spring, or Summer
    Year -- year that the survey was administered
    raw -- binary, whether the input files are raw or have been previously scored
    time_cutoff -- time cutoff to use when filtering surveys, passed to Clean_CSEM
    """

    if raw:
        df_pre = Clean_MBT(pre_file, time_cutoff = time_cutoff)
        df_post = Clean_MBT(post_file, time_cutoff = time_cutoff)

    # merge separately on full name, netID, and ID to capture as many students as possible that took both pre and posttests
    df_name = pd.merge(df_pre, df_post, how = 'inner', on = ['QA', 'QB'])
    df_netID = pd.merge(df_pre, df_post, how = 'inner', on = 'QC')
    df_studentID = pd.merge(df_pre, df_post, how = 'inner', on = 'QD')

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

    df['QC'] = df['QC'].fillna(df['QC_y']).fillna(df['QC_x'])
    df['QD'] = df['QD'].fillna(df['QD_y']).fillna(df['QD_x'])
    df['Course'] = df['Course_y'].fillna(df['Course_x'])
    df = df.drop(columns = ['QC_x', 'QC_y', 'QD_x', 'QD_y', 'QA_x', 'QA_y', 'QB_x', 'QB_y', 'Course_x', 'Course_y'])

    df['Semester'] = Semester
    df['Year'] = Year

    return df

def BuildMasterMBTDataset(dir, time_cutoff = None):
    """Construct master MBT dataset of matched and unmatched surveys

    Keyword arguments:
    dir -- directory where MBT raw files are stored
    time_cutoff -- time cutoff to use when filtering surveys, passed to Clean_CSEM
    """

    os.chdir(dir)
    pre_files = glob('RAW/**/*Pre*csv', recursive = True)
    post_files = glob('RAW/**/*Post*csv', recursive = True)

    # semester and year is in the filename, we'll just concatenate those together
    matched_dfs = [Match_MBT(pre_f, post_files[i], pre_f.split('_')[4][:2].upper(), pre_f.split('_')[-1].split('.')[0], time_cutoff = time_cutoff) for i, pre_f in enumerate(pre_files)]
    df = pd.concat(matched_dfs, axis = 0)

    df.to_csv('MBT_Master.csv', index = False)
    return df
