import os
import numpy as np
import pandas as pd
from glob import glob

# Emily Smith put together an excel file and noted the correct answers for each question as agree (A) or disagree (D)
# these commands process that excel file, strip the correct answers, and convert A to 1 and D to -1. Answers are stored in a series
Correct_Answers = pd.read_excel('C:/Users/Cole/Documents/DATA/ECLASS_DATA/Answers_Template.xlsx', sheet_name = 'Converted').iloc[[0, 2], 1:].reset_index(drop = True)
Correct_Answers.columns = Correct_Answers.iloc[1, :]
Correct_Answers = pd.Series(Correct_Answers.iloc[0, :].to_dict()).map({'A':1, 'D':-1, 'CONTROL':np.nan}).dropna()

# Natasha Holmes compiled an excel file of students that opted out of research...we need to remove those students from our dataset
Consent_df = pd.read_excel('C:/Users/Cole/Documents/DATA/MasterList.xlsx')
Consent_df['FullName'] = (Consent_df['First Name:'] + Consent_df['Last Name:']).str.lower().str.replace(' ', '')
Consent_df['Course'] = Consent_df['Course'].str.split(' ').str.get(1).apply(lambda x: 'P' + x[:-1]) # some courses were logged as Phys xxxx, others just as xxxx

def Clean_ECLASS(File, Course):
    """Filter and score E-CLASS file.

    Keyword arguments:
    File -- an E-CLASS raw csv file to process
    Course -- Cornell course where the survey was administered
    """

    Student_cols = [col for col in Correct_Answers.index if 'a' in col] # student columns ended in '_a'
    Expert_cols = [col for col in Correct_Answers.index if 'b' in col] # expert columns ended in '_b'

    df = pd.read_csv(File)
    df = df[df.loc[:, 'q40a'] == 4].drop(columns = ['q40a']) # this was a filtering question, students paying attention should have selected 4

    df['Q3_1_TEXT'] = df['Q3_1_TEXT'].str.lower().str.replace(' ', '')
    df['Q3_2_TEXT'] = df['Q3_2_TEXT'].str.lower().str.replace(' ', '')
    df['Q3_3_TEXT'] = df['Q3_3_TEXT'].apply(lambda x: x.split('@')[0].lower()).str.replace(' ', '')

    df = df.drop_duplicates(subset = ['Q3_1_TEXT', 'Q3_2_TEXT'], keep = 'last').drop_duplicates(subset = ['Q3_3_TEXT'], keep = 'last') # drop duplicated names or IDs
    df['FullName'] = (df['Q3_1_TEXT'] + df['Q3_2_TEXT']).str.lower().str.replace(' ', '')
    Opt_Outs = Consent_df.loc[(Consent_df['Course'] == Course), :] # students who opted out of research
    df = df.loc[~df['FullName'].isin(Opt_Outs), :].drop(columns = ['FullName'])

    # items are Likert and range from 1 to 5, correctness is only assessed on collapsed agree (4 or 5) or disagree (1 or 2). If the answers align (i.e., A and
    # A, then students get 1 point, if answers are opposed (i.e., A and D), then students get -1 points, and if a student selects neutral they get 0 points
    df.loc[:, Correct_Answers.index.values] = df.loc[:, Correct_Answers.index.values].apply(lambda x: x.map({1:-1, 2:-1, 3:0, 4:1, 5:1}))
    df.loc[:, Correct_Answers.index.values] = df.loc[:, Correct_Answers.index.values] * Correct_Answers

    df['Student_Score'] = df.loc[:, Student_cols].sum(axis = 1)
    df['Expert_Score'] = df.loc[:, Expert_cols].sum(axis = 1)

    return df

def MergePrePost(PreFile, PostFile, Course, Semester, Year, OutFileName = None):
    """Outer join pre and post test files together for a single course

    Keyword arguments:
    PreFile -- file path to raw pretest csv file
    PostFile -- file path to raw posttest csv file
    Course -- Cornell course where the survey was administered
    Semester -- semester that the survey was adminsitered; either Fall, Spring, or Summer
    Year -- year that the survey was administered
    OutFileName -- name of the file to write the merged dataset to
    """

    Predf = Clean_ECLASS(PreFile, Course)
    Postdf = Clean_ECLASS(PostFile, Course)

    # merge separately on full name, backwards name, and ID to capture as many students as possible that took both pre and posttests
    Full_df = pd.merge(left = Predf, right = Postdf, how = 'inner', on = ['Q3_1_TEXT', 'Q3_2_TEXT'])
    Back_df = pd.merge(left = Predf, right = Postdf, how = 'inner', left_on = ['Q3_1_TEXT', 'Q3_2_TEXT'], right_on = ['Q3_2_TEXT', 'Q3_1_TEXT'])
    ID_df = pd.merge(left = Predf, right = Postdf, how = 'inner', on = 'Q3_3_TEXT').rename(columns = {'Q3_3_TEXT':'Q3_3_TEXT_y'})

    # we make sure students aren't double counted
    Merged_df = pd.concat([Full_df, Back_df, ID_df], axis = 0, join = 'outer').drop_duplicates(subset = ['V1_x'])

    # and put back students who only took one of the pre or posttest in our dataset
    Pre_Cols = [col if col in Merged_df.columns else col + '_x' for col in Predf.columns]
    Out_Pre = Predf.loc[~Predf['V1'].isin(Merged_df['V1_x'])]
    Out_Pre.columns = Pre_Cols

    Post_Cols = [col if col in Merged_df.columns else col + '_y' for col in Postdf.columns]
    Out_Post = Postdf.loc[~Postdf['V1'].isin(Merged_df['V1_y'])]
    Out_Post.columns = Post_Cols

    Merged_df['Q3_3_TEXT'] = Merged_df['Q3_3_TEXT_y'].fillna(Merged_df['Q3_3_TEXT_x'])
    Merged_df = pd.concat([Merged_df, Out_Pre, Out_Post]).reset_index(drop = True).drop(columns = ['Q3_1_TEXT_x', 'Q3_1_TEXT_y', 'Q3_2_TEXT_x', 'Q3_2_TEXT_y', 'Q3_3_TEXT_x', 'Q3_3_TEXT_y'])

    Merged_df['Course'] = Course
    Merged_df['Semester'] = Semester
    Merged_df['Year'] = Year

    if OutFileName is not None:
        Merged_df.to_csv(OutFileName, index = False)

    return Merged_df

def BuildMasterECLASSDataset(dir):
    """Construct master E-CLASS dataset of matched and unmatched surveys

    Keyword arguments:
    dir -- directory where E-CLASS raw files are stored
    """

    os.chdir(dir)
    pre_files = glob('RAW/**/*PRE*csv', recursive = True)
    post_files = glob('RAW/**/*POST*csv', recursive = True)

    # semester and year is in the filename, we'll just concatenate those together
    matched_dfs = [MergePrePost(pre_f, post_files[i], 'P' + pre_f.split('-')[-3][-4:], pre_f.split('\\')[1][:2].upper(), pre_f.split('\\')[1][-4:]) for i, pre_f in enumerate(pre_files)]
    df = pd.concat(matched_dfs, axis = 0)

    df.to_csv('E-CLASS_Master.csv', index = False)
