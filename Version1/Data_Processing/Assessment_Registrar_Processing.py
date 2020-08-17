import os
import numpy as np
import pandas as pd

def Registrar_Processing(file, consent_file):
    """Process registrar file to match with assessment data

    Keyword arguments:
    file -- file path to registrar file
    consent_file -- file path to list of students who have opted out of research

    Note that I've also included csv files with lists of students who were taught with different lab instruction in 2017FA-1116 and 2018FA-2217. Paths to
    these files whould be confirmed.
    """

    df_registrar = pd.read_excel(file).drop(columns = ['ACT | Combined English/Writing', 'ACT | English', 'ACT | Reading', 'ACT | Writing',
                                                        'ACT | Writing Subject Score 9/15', 'SAT I | Critical Reading', 'SAT I | Read/Writing Sect Score',
                                                        'SAT I | Writing Score', 'Subject']) # we don't really care about all these reading and writing scores here
    df_registrar = df_registrar.rename(columns = {'Employee Id':'Student_ID', 'Academic Term Sdescr':'Term', 'Catalog Nbr':'Course',
                                                    'Acad Level Ldescr':'Class_Standing', 'Academic Plan':'Major', 'Effdt Gender':'Gender',
                                                    'St Urm Flag':'URM_Status', 'Student Group Sdescr':'First_Gen_Status', 'Cum GPA':'GPA'})
    df_registrar['URM_Status'] = df_registrar['URM_Status'].map({'Y':'URM', 'N':'Majority'})
    df_registrar['First_Gen_Status'] = df_registrar['First_Gen_Status'].fillna('ContGen').map({'Frst Gen':'FirstGen', 'ContGen':'ContGen'})
    df_registrar['Semester'] = df_registrar['Term'].apply(lambda x: x[-2:]) # get last two characters which are the semester
    df_registrar['Sequence'] = df_registrar['Course'].map({1112:'Engineering', 2213:'Engineering', 1116:'Honours', 2217:'Honours'})
    df_registrar['Course_Content'] = df_registrar['Course'].map({1112:'Mechanics', 2213:'EM', 1116:'Mechanics', 2217:'EM'})
    df_registrar['Class_ID'] = df_registrar['Term'] + '-' + df_registrar['Course'].astype(str) # class is unique combo of term and course
    df_registrar['Year'] = df_registrar['Term'].apply(lambda x: x[:4]).astype(str)

    df_registrar[['Course', 'Student_ID']] = df_registrar[['Course', 'Student_ID']].astype(str)
    df_registrar['Term_Number'] = df_registrar['Term'].map({'2017FA':1, '2018SP':2, '2018FA':3, '2019SP':4}) # get term order
    # if a student takes the same course more than once, drop the first
    df_registrar = df_registrar.sort_values(by = 'Term_Number').drop_duplicates(subset = ['Student_ID', 'Course'],
                                                keep = 'last').drop(columns = ['Term_Number'])

    df_consent = pd.read_excel(consent_file).drop_duplicates() # list of students who did not consent to research
    df_consent['Course'] = df_consent['Course'].str.split().str.get(1).apply(lambda x: x[:-1])
    df_consent['Net ID:'] = df_consent['Net ID:'].str.lower().str.strip(' ')

    df_registrar = df_registrar.merge(df_consent[['Net ID:', 'Course']], how = 'left', left_on = ['Netid', 'Course'], right_on = ['Net ID:', 'Course'],
                                        indicator = 'OptOut?')
    df_registrar = df_registrar.loc[df_registrar['OptOut?'] == 'left_only', :].drop(columns = ['OptOut?', 'Net ID:']) # remove students who opted out of research

    # there are some continuing ed students, students with no URM info (grad students and continuing ed students I believe), and students with no ACT/SAT math
    # info...we remove all those student. There's like 15 out of 3039 so no biggie.
    df_registrar = df_registrar[(df_registrar['Class_Standing'] == 'Fresh') | (df_registrar['Class_Standing'] == 'Sophomore') |
                               (df_registrar['Class_Standing'] == 'Junior') | (df_registrar['Class_Standing'] == 'Senior')]
    df_registrar = df_registrar[~pd.isnull(df_registrar['URM_Status'])]
    df_registrar = df_registrar[(~pd.isnull(df_registrar['ACT | Math'])) | (~pd.isnull(df_registrar['SAT I | Math'])) |
                               (~pd.isnull(df_registrar['SAT I | Math Section Score']))]

    ### convert ACT and SAT scores to percentiles using information provided by blog.prepscholar.com ###

    ACT_Math_Dict = {1:1, 2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:1, 11:1, 12:1, 13:3, 14:8, 15:18, 16:29, 17:38, 18:46, 19:51, 20:55, 21:59, 22:63, 23:68,
                        24:73, 25:78, 26:83, 27:88, 28:91, 29:93, 30:95, 31:96, 32:97, 33:98, 34:99, 35:99, 36:100}

    SAT_Math_Dict = {200:1, 210:1, 220:1, 230:1, 240:1, 250:1, 260:1, 270:1, 280:1, 290:1, 300:1, 310:1, 320:1, 330:2, 340:3, 350:4, 360:6, 370:7, 380:9,
                        390:11, 400:13, 410:15, 420:17, 430:20, 440:22, 450:25, 460:28, 470:31, 480:34, 490:37, 500:40, 510:44, 520:49, 530:53, 540:57, 550:61,
                        560:64, 570:66, 580:69, 590:72, 600:75, 610:77, 620:79, 630:81, 640:83, 650:85, 660:86, 670:88, 680:89, 690:91, 700:92, 710:93, 720:94,
                        730:95, 740:96, 750:96, 760:97, 770:98, 780:98, 790:99, 800:99}

    SAT_MathSection_Dict = {200:0, 210:1, 220:1, 230:1, 240:1, 250:2, 260:2, 270:2, 280:3, 290:3, 300:4, 310:5, 320:6, 330:7, 340:8, 350:10, 360:12, 370:14,
                                380:17, 390:19, 400:22, 410:25, 420:29, 430:32, 440:35, 450:39, 460:42, 470:46, 480:49, 490:53, 500:56, 510:59, 520:62, 530:65,
                                540:68, 550:71, 560:74, 570:76, 580:78, 590:80, 600:82, 610:84, 620:86, 630:88, 640:89, 650:91, 660:92, 670:93, 680:94, 690:95,
                                700:96, 710:96, 720:97, 730:98, 740:98, 750:98, 760:99, 770:99, 780:99, 790:99, 800:99}

    df_registrar['ACT | Math'] = df_registrar['ACT | Math'].map(ACT_Math_Dict)
    df_registrar['SAT I | Math'] = df_registrar['SAT I | Math'].map(SAT_Math_Dict)
    df_registrar['SAT I | Math Section Score'] = df_registrar['SAT I | Math Section Score'].map(SAT_MathSection_Dict)

    # if students submitted more than one score, we took the max since students can always choose not to report low scores anyway
    df_registrar['ACT_SAT_Math_Percentile'] = df_registrar[['ACT | Math', 'SAT I | Math', 'SAT I | Math Section Score']].max(axis = 1, skipna = True)

    ### collapse AP scores using cutoffs applied by Cornell when determining course credit ###

    # students can take the AB test separately or as part of the BC test, so they can have two scores... we take the max
    df_registrar['AP Calculus AB Max Score'] = df_registrar[['AP | Calculus AB Subscore Grade', 'AP | Mathematics: Calculus AB']].max(axis = 1, skipna = True)
    df_registrar['AP_Calculus_AB'] = df_registrar['AP Calculus AB Max Score'].map({0:'Poor', 1:'Poor', 2:'Poor', 3:'Poor', 4:'Well', 5:'Well'})
    df_registrar['AP_Calculus_BC'] = df_registrar['AP | Mathematics: Calculus BC'].map({0:'Poor', 1:'Poor', 2:'Poor', 3:'Poor', 4:'Well', 5:'Well'})
    df_registrar['AP_Physics_EM'] = df_registrar['AP | Physics C - Electricity & Magt'].map({0:'Poor', 1:'Poor', 2:'Poor', 3:'Poor', 4:'Poor', 5:'Well'})
    df_registrar['AP_Physics_Mech'] = df_registrar['AP | Physics C - Mechanics'].map({0:'Poor', 1:'Poor', 2:'Poor', 3:'Poor', 4:'Poor', 5:'Well'})

    df_registrar[['AP_Calculus_AB', 'AP_Calculus_BC', 'AP_Physics_EM', 'AP_Physics_Mech']] = df_registrar[['AP_Calculus_AB', 'AP_Calculus_BC', 'AP_Physics_EM',
                    'AP_Physics_Mech']].fillna('NotTaken')

    # add column to registrar data identifying the type of lab instruction students received...in 2017FA 1116 and 2018SP 2217 there was a split
    # I pulled data from files made by Emily Smith to construct lists of students in each type of lab during those semesters...confirm correctness of file paths
    df_registrar.loc[(df_registrar['Course'] == '1112') & (df_registrar['Term'] == '2019SP'), 'Instruction'] = 'New'

    df_registrar.loc[(df_registrar['Course'] == '1116') & (df_registrar['Term'] != '2017FA'), 'Instruction'] = 'New'
    FA2017_1116_Intervention = pd.read_csv('C:/Users/Cole/Documents/DATA/Fa2017-1116_ID-condition.csv')
    FA2017_1116_Intervention = FA2017_1116_Intervention.loc[FA2017_1116_Intervention['Lab.Intervention'] == 1, 'Username'] # NetID
    df_registrar.loc[(df_registrar['Course'] == '1116') & (df_registrar['Term'] == '2017FA') &
                     (df_registrar['Netid'].isin(FA2017_1116_Intervention)), 'Instruction'] = 'New'

    df_registrar.loc[(df_registrar['Course'] == '2217') & ((df_registrar['Term'] == '2018FA') | (df_registrar['Term'] == '2019SP')), 'Instruction'] = 'New'
    SP2018_2217_Intervention = pd.read_csv('C:/Users/Cole/Documents/DATA/Sp2018_2217_ID-condition.csv')
    SP2018_2217_Intervention = SP2018_2217_Intervention.loc[SP2018_2217_Intervention['Lab.Condition'] == 'I', 'Username'] # NetID
    df_registrar.loc[(df_registrar['Course'] == '2217') & (df_registrar['Term'] == '2018SP') &
                        (df_registrar['Netid'].isin(SP2018_2217_Intervention)), 'Instruction'] = 'New'

    # all the courses I haven't identified as 'New' are 'Old'
    df_registrar['Instruction'] = df_registrar['Instruction'].fillna('Old')

    # a couple final tweaks to line up with conventions I've used with assessment data
    df_registrar['Course'] = 'P' + df_registrar['Course']

    return(df_registrar)

def Process_PLIC(df_Complete, Class_ID, Year, Semester, Course):
    df = df_Complete[df_Complete['Class_ID'] == Class_ID]
    df['Course'] = Course
    df['Semester'] = Semester
    df['Year'] = Year
    df.loc[df['Survey_x'] == 'F', 'PreScores'] = np.nan # the PLIC had some response surveys that we'll treat as missing
    df.loc[df['Survey_y'] == 'F', 'PostScores'] = np.nan
    df = df[~(pd.isnull(df['PreScores'])) | ~(pd.isnull(df['PostScores']))].reset_index(drop = True) # we only need entries where there was at least one score
    df['Q5a_x'] = df['Q5a_x'].astype(str).str.split('@').str.get(0).str.lower()
    df['Q5a_y'] = df['Q5a_y'].astype(str).str.split('@').str.get(0).str.lower()
    df['Student_ID'] = df['Q5a_y'].fillna(df['Q5a_x'])
    return df[['Student_ID', 'PreScores', 'PostScores', 'Semester', 'Course', 'Year']]

def Registrar_Merge(assessment_file, assessment, registrar_file, consent_file):

    df_Registrar = Registrar_Processing(registrar_file, consent_file)
    df = pd.read_csv(assessment_file)
    if(assessment == 'CSEM'):
        df['IntendedMajor'] = ''
        df = df[['NetID', 'Q39', 'Total_Score_x', 'Total_Score_y', 'Semester', 'Course', 'Year']].rename(columns = {'NetID':'Netid', 'Q39':'Student_ID',
                                                                                                                    'Total_Score_x':'PreScores',
                                                                                                                    'Total_Score_y':'PostScores'})
    elif(assessment == 'ECLASS'):

        conditions = [
                        (df['Q47'] == 1) | (df['Q47'] == 6) | (df['Q47'] == 7) | (df['Q47'] == 8) | (df['Q47'] == 9),
                        df['Q47'] < 14
                        ]
        output = [
                    'Physics',
                    'EngineeringOrOtherSci'
                    ]

        df['IntendedMajor'] = np.select(conditions, output, None) # in v2 of this paper we focus on this variable and the E-CLASS
        df = df[['Q3_3_TEXT', 'Student_Score_x', 'Student_Score_y', 'IntendedMajor', 'Semester', 'Course', 'Year']].rename(columns = {'Q3_3_TEXT':'Student_ID',
                                                                                                                                        'Student_Score_x':'PreScores',
                                                                                                                                        'Student_Score_y':'PostScores'})
    elif(assessment == 'MBT'):
        df['IntendedMajor'] = ''
        df = df[['QC', 'QD', 'Total_Score_x', 'Total_Score_y', 'Semester', 'Course', 'Year']].rename(columns = {'QC':'Netid', 'QD':'Student_ID',
                                                                                                                'Total_Score_x':'PreScores',
                                                                                                                'Total_Score_y':'PostScores'})
    else: # we build the master PLIC dataset elsewhere, but we only need Cornell classes here, so we'll fetch those
        Fall2017_1112 = Process_PLIC(df, 'R_2xOT2Y1NtNiseCk', '2017', 'FA', 'P1112')
        Fall2017_2213 = Process_PLIC(df, 'R_zfk080BHz6RWixb', '2017', 'FA', 'P2213')
        Fall2017_1116 = Process_PLIC(df, 'R_1Oko8BpPfb9rt0G', '2017', 'FA', 'P1116')
        Fall2017_2217 = Process_PLIC(df, 'R_12QFe4VQPh6oNW1', '2017', 'FA', 'P2217')

        Spring2018_1112 = Process_PLIC(df, 'R_1LHvn3R5Afj8eUc', '2018', 'SP', 'P1112')
        Spring2018_1116 = Process_PLIC(df, 'R_2R8MnTyv2jFgPzA', '2018', 'SP', 'P1116')

        Fall2018_1112 = Process_PLIC(df, 'R_3ijRcPfXo8MUfFj', '2018', 'FA', 'P1112')
        Fall2018_1116 = Process_PLIC(df, 'R_1IB300CxBKh0Tw7', '2018', 'FA', 'P1116')

        Spring2019_1112 = Process_PLIC(df, 'R_RKRNIWFu1gZuSPf', '2019', 'SP', 'P1112')

        df = pd.concat([Fall2017_1112, Fall2017_2213, Fall2017_1116, Fall2017_2217, Spring2018_1112, Spring2018_1116, Fall2018_1112, Fall2018_1116,
                        Spring2019_1112]).reset_index(drop = True)
        df['IntendedMajor'] = ''

    df['Year'] = df['Year'].astype(str) # being read as int and wouldn't merge
    df1 = pd.merge(df, df_Registrar, on = ['Course', 'Year', 'Semester', 'Student_ID'], how = 'inner')
    if((assessment == 'ECLASS') | (assessment == 'PLIC')): # these assessments only have the one ID column and sometimes use student ID and sometimes NetID
        df2 = pd.merge(df, df_Registrar, left_on = ['Course', 'Year', 'Semester', 'Student_ID'], right_on = ['Course', 'Year', 'Semester', 'Netid'],
                        how = 'inner').rename(columns = {'Student_ID_y':'Student_ID'})
    else:
        df2 = pd.merge(df, df_Registrar, on = ['Course', 'Year', 'Semester', 'Netid'], how = 'inner').rename(columns = {'Student_ID_y':'Student_ID'})

    df_merged = pd.concat([df1, df2]).drop_duplicates(subset = ['Course', 'Year', 'Semester', 'Student_ID'], keep = 'last').reset_index(drop = True)

    index_vals = [tuple(v) for v in df_merged[['Course', 'Year', 'Semester', 'Student_ID']].values] # students that are in assessment dataset
    # get dataframe of students in registrar data that were registered for classes present in the assessment dataset
    df_courses = df_Registrar.loc[(df_Registrar['Course'] + '-' + df_Registrar['Year'] + '-' + df_Registrar['Semester']).isin(df_merged['Course'] + '-' +
                                    df_merged['Year'] + '-' + df_merged['Semester'])].set_index(['Course', 'Year', 'Semester', 'Student_ID'])
    filtered = df_courses.loc[~df_courses.index.isin(index_vals)].reset_index() # get students that are not in the merged dataset

    df_out = pd.concat([df_merged, filtered]).reset_index(drop = True)
    df_out['Assessment'] = assessment
    df_out = df_out.loc[:, ['Student_ID', 'Netid', 'Course', 'Class_Standing', 'Major', 'Gender', 'URM_Status', 'First_Gen_Status', 'GPA',
                            'ACT_SAT_Math_Percentile', 'AP_Calculus_AB', 'AP_Calculus_BC', 'AP_Physics_EM',	'AP_Physics_Mech', 'PreScores', 'PostScores',
                            'Assessment', 'Semester', 'Sequence', 'Course_Content', 'Instruction', 'IntendedMajor', 'Class_ID']]

    return df_out

def Get_OVB_Master(CSEM_file, ECLASS_file, MBT_file, PLIC_file, Registrar_file, Consent_file, outfile):

    df_CSEM = Registrar_Merge(CSEM_file, 'CSEM', Registrar_file, Consent_file)
    df_ECLASS = Registrar_Merge(ECLASS_file, 'ECLASS', Registrar_file, Consent_file)
    df_MBT = Registrar_Merge(MBT_file, 'MBT', Registrar_file, Consent_file)
    df_PLIC = Registrar_Merge(PLIC_file, 'PLIC', Registrar_file, Consent_file)

    df = pd.concat([df_CSEM, df_ECLASS, df_MBT, df_PLIC], axis = 0).reset_index(drop = True)
    df.to_csv(outfile, index = False)

    return df
