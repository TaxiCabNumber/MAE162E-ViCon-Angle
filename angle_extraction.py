import pandas as pd
import numpy as np
import os

def read_split_csv(file_name): #accepts res[i]
    df = pd.read_csv(dir_path+'/'+file_name, header=None, skiprows=lambda x: (x<2 or x==4), usecols=[i for i in range(2,38)])
    # fix NaN, extract non NaN values into list, then populate columns 3 at a time
    df.columns = range(df.columns.size)
    for i in range(12):
        df.iloc[0,3*i+1] = df.iloc[0,3*i]
        df.iloc[0,3*i+2] = df.iloc[0,3*i]
    # dataframe column header
    head_proto = [[],[]]
    # combine first 2 rows into one string (OriginRotationX,...starfishRotationX,...  )
    for i in range(2):
        head_proto[i] = df.loc[[i]].values.flatten().astype(str).tolist() 
    head = list(map("".join, zip(*head_proto))) # use concatenated str as df column headers
    for i in range(len(head)):
        head[i] = head[i][9:]
    df = df.set_axis(head, axis=1)  
    # remove non-data rows, fix row indices, remove extra index column generated
    df = df.drop([0,1]) #drop rows that contained column header
    df.reset_index()
    df = df.astype(float) 
    # sub-df for markers
    df_torso = df.loc[:,'torso1X':'torso3Z']
    #print(df_torso)
    df_brace = df.loc[:,['arm1X','arm1Y','arm1Z','shoulder1X','shoulder1Y','shoulder1Z','shoulder2X','shoulder2Y','shoulder2Z']]
    #print(df_brace)
    df_arm = df.loc[:,'arm2X':'arm4Z']
    #print(df_arm)
    return df_torso, df_brace, df_arm

# gsheet row names = file names in os.listdir
# iterate through file names to truncate each corresponding file's data
def trunc_avg_data(torso_df, brace_df, arm_df, start, end):
    torso_trial = torso_df.iloc[start:end,:].mean(axis=0).to_frame().T
    brace_trial = brace_df.iloc[start:end,:].mean(axis=0).to_frame().T
    arm_trial = arm_df.iloc[start:end,:].mean(axis=0).to_frame().T
    return torso_trial, brace_trial, arm_trial

    # shorten data frame to corresponding rows
def plane_normal(xyz_df):
    p1 = xyz_df.iloc[:,0:3]
    p2 = xyz_df.iloc[:,3:6]
    p3 = xyz_df.iloc[:,6:9]
    d1 = dict(zip(p1.columns, p3.columns))
    d2 = dict(zip(p2.columns, p3.columns))
    p1 = p1.rename(columns=d1)
    p1 = p1.astype(float)
    p2 = p2.rename(columns=d2)
    p2 = p2.astype(float)
    p3 = p3.astype(float)
    v1 = p1.subtract(p3).to_numpy()
    v2 = p2.subtract(p3).to_numpy()
    plane_coef = np.cross(v1,v2)[0]
    return plane_coef

def plane_angle(plane1, plane2):
    import math
    a1 = plane1[0]
    b1 = plane1[1]
    c1 = plane1[2]
    a2 = plane2[0]
    b2 = plane2[1]
    c2 = plane2[2]
    d = ( a1 * a2 + b1 * b2 + c1 * c2 )
    e1 = math.sqrt( a1 * a1 + b1 * b1 + c1 * c1)
    e2 = math.sqrt( a2 * a2 + b2 * b2 + c2 * c2)
    d = d / (e1 * e2)
    A = math.degrees(math.acos(d))
    return A

# read csv files from path
dir_path = os.getcwd() + r'\Vicon Data'
# list to store files
res = []
names = []
# Iterate directory
for file in os.listdir(dir_path):
    # check only text files
    if file.endswith('.csv'):
        res.append(file)
        names.append(file)
# iterate through list and convert, start with first file to test (for csv in res: )
# check
index_path = os.getcwd() + r'\trial_indices.csv'
index_df = pd.read_csv(index_path)
index_df = index_df.set_index('File Name')
index_df.index.names = [None]
# reduce each file to 100 rows based on trialindices.csv
angle_list = []
for i in range(len(res)):
    torso_trial, brace_trial, arm_trial = read_split_csv(res[i]) #per trial
    start = index_df.loc[res[i],'Start Frame'] #select row according to file name
    end = index_df.loc[res[i],'End Frame'] #select row according to file name
    torso_avg, brace_avg, arm_avg = trunc_avg_data(torso_trial, brace_trial, arm_trial, start, end)
    norm_torso = plane_normal(torso_avg)
    norm_brace = plane_normal(brace_avg)
    norm_arm = plane_normal(arm_avg)
    angle_arm_brace = plane_angle(norm_arm, norm_brace)
    angle_brace_torso = plane_angle(norm_brace, norm_torso)
    angle_arm_torso = plane_angle(norm_arm, norm_torso)
    angle_list.append([res[i], angle_arm_brace, angle_brace_torso, angle_arm_torso])
angle_df = pd.DataFrame(angle_list)
angle_col = ['File Name','angle_arm_brace','angle_brace_torso','angle_arm_torso']
labels = dict(zip(angle_df.columns, angle_col))
angle_df = angle_df.rename(columns=labels)
angle_df.to_csv(os.getcwd()+'/'+'sling_angles.csv', index=False) #save angles_df as csv