from flask import Flask, request, Response, json
import numpy as numpy
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
import sqlite3


#create flask instance
app = Flask(__name__)

#create api
@app.route('/api', methods=['GET', 'POST'])
def getskills():
    def buildsklist(sktype,dtype):
        if sktype == 'H':
            selsk_stmt = '''SELECT Skill_ID, Description FROM Skills WHERE TYPE IN ('cs','ds','pltfm','stat','tech') ORDER BY DESCRIPTION;'''
        else:
            selsk_stmt = '''SELECT Skill_ID, Description FROM Skills WHERE TYPE IN ('ba','domn','nontech') ORDER BY DESCRIPTION;'''

# build skill dictionary {..."2":"Agile",...}
# technical
        conn = sqlite3.connect('.\\JobSkill.db')
        curs = conn.cursor()
        curs.execute(selsk_stmt)
        skdescs = curs.fetchall()
        skmIDs = ''
        skills = ''
        for skid, skdesc in skdescs:
            if skmIDs == '':
                skmIDs = str(skid)
            else:
                skmIDs = skmIDs + ',' + str(skid)
            
            if skills == '':
                skills = skdesc
            else:
                skills = skills + ',' + skdesc

        if dtype == 'I':
            return skmIDs
        else:
            return skills
# main
    sktype = 'H'
    skills = buildsklist(sktype,'D') # build hard skill description list
    outdict = dict(Hardskills=skills)    
    sktype = 'S'
    skills = buildsklist(sktype,'D') # build soft skill description list
    outdict2 = dict(Softskills=skills)
    outdict.update(outdict2)    
    return Response(json.dumps(outdict)) 

@app.route('/getjobs', methods=['GET', 'POST'])
def getjobs(): 
    
# get requested skill set input and post jobs requiring these skill set
    mode = 'unittest'
    if mode != 'unittest':
        data = request.get_json(force=True)
    else:
        skreq = "Modeling,Statistics,Communication"
        input_data = json.dumps({"skills": skreq})
        data = json.loads(input_data)

    requestData = data["skills"]

#print(requestData)
# sktype: 'H'ard or 'S'oft skill
# dtype: 'I'D of skill or 'D'escription of skill
    def buildsklist(sktype,dtype):
        if sktype == 'H':
            selsk_stmt = '''SELECT Skill_ID, Description FROM Skills WHERE TYPE IN ('cs','ds','pltfm','stat','tech') ORDER BY DESCRIPTION;'''
        else:
            selsk_stmt = '''SELECT Skill_ID, Description FROM Skills WHERE TYPE IN ('ba','domn','nontech') ORDER BY DESCRIPTION;'''

# build skill dictionary {..."2":"Agile",...}
# technical  
        conn = sqlite3.connect('.\\JobSkill.db')
        curs = conn.cursor()      
        curs.execute(selsk_stmt)
        skdescs = curs.fetchall()
    
        skmIDs = ''
        skills = ''
        for skid, skdesc in skdescs:
#         print(skid,' ',skdesc)
            if skmIDs == '':
                skmIDs = str(skid)
            else:
                skmIDs = skmIDs + ',' + str(skid)
            
            if skills == '':
                skills = skdesc
            else:
                skills = skills + ',' + skdesc
#     print(skmIDs)       
#     print(skills)
        if dtype == 'I':
            return skmIDs
        else:
            return skills    

# #requestData = numpy.reshape(requestData, (1, -1))
# #print(type(requestData),requestData) 
# Select all SkillJobs rows
    sjsel_stmt = '''SELECT SkillsJobs_ID, SkillIDs, JobIDs FROM SkillsJobs;'''
    conn = sqlite3.connect('.\\JobSkill.db')
    curs = conn.cursor()
    curs.execute(sjsel_stmt)
    sjs = curs.fetchall()
    conn.commit()

# convert request json to skill IDs list
    sks = {}
    selsk_stmt = '''SELECT Skill_ID, Description FROM Skills ORDER BY Skill_ID;'''
    for skkey, skval in curs.execute(selsk_stmt):
        sks[skkey] = skval
    skkey_list = list(sks.keys())
    skval_list = list(sks.values())

# get hard and soft skills list
    hsklist = buildsklist('H','I')
    ssklist = buildsklist('S','I')
    hsktcnt = hsklist.count(',')+1
    ssktcnt = ssklist.count(',')+1

#  build user input skill list
    skids = ''
    for skill1 in requestData.split(","):
        position = skval_list.index(skill1.lower())
        skid = skkey_list[position]
        if skids == '':
            skids = str(skid)
        else:
            skids = skids + ',' + str(skid)

# search input skills in each SkillsJobs row, if found, 
# append title, company, location, skills required, % match 
# to response list
# process each SkillsJobs row
    jsel_stmt = '''SELECT JobTitle, Company, Location, URL FROM Jobs WHERE Job_ID = ?;'''
    outdicts = ''
    for sj in sjs:                          # loop through each SkillsJobs, get a skill job record
        sjIDs = sj[0]
        sjskIDs = sj[1]
        sjjobIDs = sj[2]
        thskcnt = 0
        tsskcnt = 0
        tskcnt = 0
        # get job total hard skill, soft skill and all skills count, by loop through each skill on skill job record
        for skid2 in sjskIDs.split(','):
            tskcnt += 1
            for hid2 in hsklist.split(','): 
                if skid2 == hid2: thskcnt += 1
            for sid2 in ssklist.split(','):
                if skid2 == sid2: tsskcnt += 1
        skdesc = ''
# process each input skill
        hskcnt = 0
        sskcnt = 0
        skcnt = 0  
        for skill2 in skids.split(','):          # loop through user skills        
            if skill2 in sjskIDs:                # if user skill in job skills            
                for hsk in hsklist.split(','):   # check if it's a hard skill            
                    if skill2 == hsk:
                        hskcnt += 1              # increment user hard skill match count
                for ssk in ssklist.split(','):   # check if it's a soft skill
                    if skill2 == ssk:
                        sskcnt += 1
        skcnt = hskcnt+sskcnt                    # total user skill count match with skills on skill job record
        if skcnt > 0:                            # if user skill matches in skills of the skill job record       
            # build job skills desc list
            for skill3 in sjskIDs.split(','):
                skill3 = int(skill3.strip())
                position = skkey_list.index(skill3)
                jsval = skval_list[position]
                if skdesc == '':
                    skdesc = jsval
                else:
                    skdesc = skdesc+ ','+jsval
            # get title, company, location, url        
            for jobID in sjjobIDs:      
                curs.execute(jsel_stmt, (jobID))
                jrec = curs.fetchone()
                if jrec is not None: 
                    title = jrec[0]
                    company = jrec[1]
                    location = jrec[2]
                    url = jrec[3]
                    hpercent = int(hskcnt / thskcnt * 100)
                    spercent = int(sskcnt / tsskcnt * 100)
                    opercent = int(skcnt / tskcnt * 100)
                    outdict = dict(Title=title, Company=company, Location=location, Skills=skdesc, URL=url, \
                               HPercent=hpercent, SPercent=spercent,OPercent=opercent)
                    outline = title+','+company+','+location+',"'+skdesc+'",'+url+','+str(hpercent)\
                                +','+str(spercent)  +','+str(opercent)                             

                    if outdicts == '':
                        outdicts = str(outdict)
                    else:
                        outdicts = outdicts+','+str(outdict)
    # response = json.dumps(outdicts)
    # print(response)

    return Response(json.dumps(outdicts))
@app.route('/getasoc', methods=['GET', 'POST'])
def getasoc():
    
# get request from and post response to web user interface app
# Connect to SQLite3 database, select all SkillsJobs rows
    conn = sqlite3.connect('.\\JobSkill.db')
    curs = conn.cursor()
# Select all SkillJobs rows
    assocsel_stmt = '''SELECT skDesc1, skDesc2, confidence, lift FROM JobSkillPairs ORDER BY confidence desc;'''
    curs.execute(assocsel_stmt)
    assocs = curs.fetchall()
    conn.commit()
    
    outdicts = ''
    for assoc in assocs:
        skdesc1 = assoc[0]
        skdesc2 = assoc[1]
        confidence = assoc[2]
        lift = assoc[3] 
        outdict = dict(Skill1=skdesc1, Skill2=skdesc2, Confidence=confidence, Lift=lift)
        print(outdict)
        if outdicts == '':
            outdicts = str(outdict)
        else:
            outdicts = outdicts+','+str(outdict)
    # response = json.dumps(outdicts)
    # print(response)
    return Response(json.dumps(outdicts)) 
      
if __name__ == '__main__':
    app.run()

