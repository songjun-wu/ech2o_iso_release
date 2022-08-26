#    !/usr/bin/env python3
# -*- coding: utf-8 -*-
# *************************************************
#
# Model-data misfit after Monte-Carlo sampling +
# assemble parameters samples
#
# -------
# Author: S. Kuppel
# Created on 10/2016
# -------------------------------------------------

import numpy as np
from datetime import datetime, timedelta
import os, time, sys, glob, copy
import json
from optparse import OptionParser

# --- Subroutine(s)
import eval_measures as metrics

parser = OptionParser()

# Switch : fetching obs metrics or corresponding parameters / best runs ?
# 0 = metrics + par, 1 = best runs
parser.add_option("--switch",dest="switch",metavar="SWITCH")
parser.add_option("--ext",dest="ext",metavar="EXT")
parser.add_option("--byjob",dest="byjob",metavar="byjob")
parser.add_option("--docopy",dest="docopy",metavar="docopy")
parser.add_option("--clean",dest="clean",metavar="clean")
parser.add_option("--jobs",dest="jobs",metavar="jobs")

(options, args) = parser.parse_args()

switch = int(options.switch)
MCname = copy.copy(options.ext)
if options.docopy != None:
    docopy = int(options.docopy)
else:
    docopy = 0
if options.clean != None:
    clean = int(options.clean)
else:
    clean = 0
if options.byjob != None:
    byjob = int(options.byjob)
else:
    byjob = 0

#switch = 1
#swpar = 1
#swsim = 1
#nbest = 30

# scratch directory
scrdir = '/scratch/users/s01ks6'

# -- Output directory
outdir = 'Outputs'

# -- Date set-up
tstart = datetime(2013,2,21) # start of 'useful' sim
leff = 1265 # useful sim length
spinup = 0#1095 # spinup length
lsim = leff + spinup # total sim length
simt = [tstart-timedelta(days=spinup)+timedelta(days=x) for x in range(lsim)]

# --- Definition ---

# Path to data
obsdir = '/users/s01ks6/Data/BB'
# Simulation subdirectories
#MCname = 'MC12'
# Observations
obsnames = ['dD_Stream','d18O_Stream',
            'dD_Peat.L1','d18O_Peat.L1.tab',
            'dD_Gley.L1','d18O_Gley.L1.tab',
            'dD_Podzol.L1','d18O_Podzol.L1',
            'dD_SForest.L1','d18O_SForest.L1',
            'dD_NForest.L1','d18O_NForest.L1',
            'dD_SHeather.L1','d18O_SHeather.L1',
            'dD_NHeather.L1','d18O_NHeather.L1',
            'dD_SForest.T','d18O_SForest.T',
            'dD_NForest.T','d18O_NForest.T',
            'dD_SHeather.T','d18O_SHeather.T',
            'dD_NHeather.T','d18O_NHeather.T',
            'dD_DW1','d18O_DW1',
            'dD_DW2','d18O_DW2',
            'dD_DW3','d18O_DW3',
            'dD_DW4','d18O_DW4']

#'SaturationArea']#,'SWC_forest','T_forest']
nobs = len(obsnames)

# Corresponding simulations outputs
simdir = os.getcwd()+'/'+MCname+'_sampling.'
simfiles = ['dD_Stream_all.tab','d18O_Stream_all.tab',
            'dD_Peat.L1_all.tab','d18O_Peat.L1_all.tab',
            'dD_Gley.L1_all.tab','d18O_Gley.L1_all.tab',
            'dD_Podzol.L1_all.tab','d18O_Podzol.L1_all.tab',
            'dD_SForest.L1_all.tab','d18O_SForest.L1_all.tab',
            'dD_NForest.L1_all.tab','d18O_NForest.L1_all.tab',
            'dD_SHeather.L1_all.tab','d18O_SHeather.L1_all.tab',
            'dD_NHeather.L1_all.tab','d18O_NHeather.L1_all.tab',
            'dD_SForest.T_all.tab','d18O_SForest.T_all.tab',
            'dD_NForest.T_all.tab','d18O_NForest.T_all.tab',
            'dD_SHeather.T_all.tab','d18O_SHeather.T_all.tab',
            'dD_NHeather.T_all.tab','d18O_NHeather.T_all.tab',
            'dD_DW1_all.tab','d18O_DW1_all.tab',
            'dD_DW2_all.tab','d18O_DW2_all.tab',
            'dD_DW3_all.tab','d18O_DW3_all.tab',
            'dD_DW4_all.tab','d18O_DW4_all.tab']
            #'SaturationArea_all.tab']
pardir = os.getcwd()+'/Parameters_samples/'#+MCname+'_sampling_parameters.1.txt'

# Obs filenames
obsfiles = ['/Isotopes/dD_Stream_01062011-19092016.csv','/Isotopes/d18O_Stream_01062011-19092016.csv',
            '/Isotopes/dD_Peat.csv','/Isotopes/d18O_Peat.csv',
            '/Isotopes/dD_Gley.csv','/Isotopes/d18O_Gley.csv',
            '/Isotopes/dD_Podzol.csv','/Isotopes/d18O_Podzol.csv',
            '/Isotopes/dD_ForestA.csv','/Isotopes/d18O_ForestA.csv',
            '/Isotopes/dD_ForestB.csv','/Isotopes/d18O_ForestB.csv',
            '/Isotopes/dD_HeatherA.csv','/Isotopes/d18O_HeatherA.csv',
            '/Isotopes/dD_HeatherB.csv','/Isotopes/d18O_HeatherB.csv',
            '/Groundwater/dD_deeperwells.csv','/Groundwater/d18O_deeperwells.csv',
            '/Groundwater/dD_deeperwells.csv','/Groundwater/d18O_deeperwells.csv',
            '/Groundwater/dD_deeperwells.csv','/Groundwater/d18O_deeperwells.csv',
            '/Groundwater/dD_deeperwells.csv','/Groundwater/d18O_deeperwells.csv']

# columns in files and depths for soil
obscol = obsdph = {}
obscol['dD_Stream'] = obscol['d18O_Stream'] = 1

obscol['dD_Peat.L1'] = obscol['d18O_Peat.L1'] = [1,2]
obsdph['dD_Peat.L1'] = obsdph['d18O_Peat.L1'] = [0.1,0.2]

obscol['dD_Gley.L1'] = obscol['d18O_Gley.L1'] = obscol['dD_Podzol.L1'] = obscol['d18O_Podzol.L1'] = [1,2,3]
obsdph['dD_Gley.L1'] = obsdph['d18O_Gley.L1'] = obsdph['dD_Podzol.L1'] = obsdph['d18O_Podzol.L1'] = [0.1,0.2,0.4]

obscol['dD_SForest.L1'] = obscol['d18O_SForest.L1'] = [1,2,3,4,5,6,7,8]
obsdph['dD_SForest.L1'] = obsdph['d18O_SForest.L1'] = [0.025,0.075,0.1,0.125,0.175,0.2,0.25,0.4]

obscol['dD_NForest.L1'] = obscol['d18O_NForest.L1'] = obscol['dD_SHeather.L1'] = obscol['d18O_SHeather.L1'] = obscol['dD_NHeather.L1'] = obscol['d18O_NHeather.L1'] = [1,2,3,4]
obsdph['dD_NForest.L1'] = obsdph['d18O_NForest.L1'] = obsdph['dD_SHeather.L1'] = obsdph['d18O_SHeather.L1'] = obsdph['dD_NHeather.L1'] = obsdph['d18O_NHeather.L1'] = [0.025,0.75,0.125,0.175]

obscol['dD_SForest.T'] = obscol['d18O_SForest.T'] = 1
obscol['dD_NForest.T'] = obscol['d18O_NForest.T'] = 2
obscol['dD_SHeather.T'] = obscol['d18O_SHeather.T'] = 3
obscol['dD_NHeather.T'] = obscol['d18O_NHeather.T'] = 4

obscol['dD_DW1'] = obscol['d18O_DW1'] = 1
obscol['dD_DW2'] = obscol['d18O_DW2'] = 1
obscol['dD_DW3'] = obscol['d18O_DW3'] = 1
obscol['dD_DW4'] = obscol['d18O_DW4'] = 1

#1]
# Number of samples
nit = 1786
# Number of parallel runs
print options.jobs
if byjob == 1 and options.jobs != None:
    jobs = [int(x) for x in options.jobs.split(',')]
else:
    jobs = [13,14,15]
print jobs
#sys.exit()
#jobs = [24,25,27]
#jobs = [31,32,33]
#jobs = [35,36,37]
#jobs = [38,39,40,43]
#jobs = [45,46,48]
#jobs = [52,57,14]
#jobs = [50]
#jobs = [5]
#jobs = [47]
#jobs = [54,79,81]
#jobs = [7,9,51,59]
#jobs = [63,66,78]
#jobs = [82,83,84,80]
#jobs = [49,53,55]
#jobs = [56, 58, 60]
#jobs = [61, 62, 64, 8]
#jobs = [65, 67, 68]
#jobs = [69, 70, 71]
#jobs = [72, 73, 74]
#jobs = [75, 76, 77]
#jobs = [8,2,1]
#jobs = [10,3]
#jobs = [2]
#jobs = [10]
#jobs=[14]

# Time frames used for the metrics
fitbeg = [datetime(2013,2,21), # flow
          datetime(2013,2,21),datetime(2013,2,21),datetime(2013,2,21),datetime(2013,2,21),datetime(2015,2,25), #SWC
          datetime(2015,7,8),datetime(2016,4,1),datetime(2015,7,31),datetime(2015,7,31),datetime(2015,7,31),datetime(2015,7,31), # T and ET
          datetime(2014,7,17),datetime(2014,7,17),datetime(2015,4,17), # NR
          datetime(2013,2,21),datetime(2013,2,21), # iso flow
          datetime(2015,6,9),datetime(2015,6,9),datetime(2015,7,9),#iso DW1
          datetime(2015,6,9),datetime(2015,6,9),datetime(2015,7,9),#iso DW2
          datetime(2015,6,9),datetime(2015,6,9),datetime(2015,7,9),#iso DW3
          datetime(2015,6,9),datetime(2015,6,9),datetime(2015,7,9)] #iso DW4
          
          #datetime(2012,11,1)]
fitend = [datetime(2015,2,20),
          datetime(2015,2,20),datetime(2015,2,20),datetime(2015,2,20),datetime(2015,2,20),datetime(2016,2,23),
          datetime(2015,9,28),datetime(2016,8,8),datetime(2015,10,31),datetime(2015,10,31),datetime(2015,10,31),datetime(2015,10,31),
          datetime(2015,7,16),datetime(2015,7,16),datetime(2016,4,15),
          datetime(2015,2,20),datetime(2015,2,20),
          datetime(2016,8,8),datetime(2016,8,8),datetime(2016,8,8),
          datetime(2016,8,8),datetime(2016,8,8),datetime(2016,8,8),
          datetime(2016,8,8),datetime(2016,8,8),datetime(2016,8,8),
          datetime(2016,8,8),datetime(2016,8,8),datetime(2016,8,8)]
          #datetime(2013,10,31)]

# Metrics
#metrics = ['CF_MSE','CF_NSE']
#nmet = len(metrics

print '========================================'
print '------ Calculating model-data fits -----'
print
print " Namely: KGE, MAE, RMSE, and Pearson's r"
print 
print 'Obsversations used here:'
for i in range(nobs):
    print obsnames[i]+': from',fitbeg[i],'to',fitend[i]
print
print 'MC jobs included here:'
print ' '.join([str(i) for i in jobs]) 
print


#############################################################################################
# Simulations outputs : saving the metrics
# if switch == 0:

#print
#print 'Summarizing the metrics....'
print

obs={}
obst={}
nok = 0

if switch == 0:

    print 'Get observations...'
    print

    for iobs in range(nobs):
        
        #print obsnames[iobs]
        # -- Get the obs
        f_obs = obsdir+obsfiles[iobs]
        tmp = np.genfromtxt(f_obs,delimiter=',',skip_header=1,unpack=True, dtype= '|S10')[0]
        tmpt = np.array([datetime.strptime(a, '%d/%m/%Y') for a in tmp])
        lobs = len(tmpt)
        tmp = np.genfromtxt(f_obs,delimiter=',',skip_header=1,unpack=True)[obscol[iobs]]
        # Crop obs between desired time frame
        obs[obsnames[iobs]] = [tmp[idx] for idx in range(lobs) if tmpt[idx]>=fitbeg[iobs] and tmpt[idx]<=fitend[iobs]]
        obst[obsnames[iobs]] = np.array([tmpt[idx] for idx in range(lobs) if tmpt[idx]>=fitbeg[iobs] and tmpt[idx]<=fitend[iobs]])
    
    # -- Copy simulations outputs to scratch
    if docopy == 1:
        print 'Temporarily copy parameters to scratch...(outputs will done on-the-fly for each job)'
    
        tmpdir = os.path.abspath(os.path.join(scrdir,MCname))
        if len(glob.glob(tmpdir))==0:
            os.system('mkdir '+tmpdir)
        tmppar = tmpdir+'/'+MCname+'_parameters'
        if len(glob.glob(tmppar))==0:
            os.system('mkdir '+tmppar)
        os.system('cp -p '+pardir+'/'+MCname+'_sampling_parameters.*.txt '+tmppar+'/')

        #print 'Job ',
        #for i in range(1,njob):
            #print str(i)+'...',
            #tmpdir2 = tmpdir+'/'+MCname+'_sampling.'+str(i)
            #if len(glob.glob(tmpdir2))==0:
            #    os.system('mkdir '+tmpdir2)
            #os.system('cp -p '+simdir+str(i)+'/*.tab '+tmpdir2+'/')


    print
    print 'Preparing summary files...'

    # -- Headers of summary files (all jobs together)
    if byjob == 0:
        # Metrics
        with open(tmpdir+'/'+MCname+'_KGE2012.txt','w') as f_out:
            f_out.write('Job,Iteration,Sample,'+','.join([x for x in obsnames])+'\n')
        with open(tmpdir+'/'+MCname+'_MAE.txt','w') as f_out:
            f_out.write('Job,Iteration,Sample,'+','.join([x for x in obsnames])+'\n')
        with open(tmpdir+'/'+MCname+'_RMSE.txt','w') as f_out:
            f_out.write('Job,Iteration,Sample,'+','.join([x for x in obsnames])+'\n')
        with open(tmpdir+'/'+MCname+'_corr.txt','w') as f_out:
            f_out.write('Job,Iteration,Sample,'+','.join([x for x in obsnames])+'\n')
    # Parameters
    f_in = tmppar+'/'+MCname+'_sampling_parameters.char.txt'
    tmp = list(np.genfromtxt(f_in,delimiter=',',dtype= '|S20',unpack=True,skip_header=1)[0])
    #print tmp
    npar = len(tmp)
    print
    print '(length of parameter vector: '+str(npar)+')'
    print
    pnames = ','.join([str(tmp[idx]) for idx in range(npar)])
    if byjob == 0:
        with open(tmpdir+'/'+MCname+'_parameters.txt','w') as f_out:
            f_out.write('Job,Iteration,Sample,'+pnames+'\n')

    # initialize costfunction
    KGE = {}
    MAE = {}
    RMSE = {}   
    corr = {}
    
    itot = 1
    itot2 = 1

    print 'Calculate sample misfits...'

    for i in jobs:
        
        print i,'...',

        #### Quickly get the runs tht worked
        f_sim = simdir+str(i)+'/'+simfiles[0]
        js1 = np.genfromtxt(f_sim,delimiter=',',skip_header=1,unpack=True,dtype=np.int)[0]
        nj1 = len(js1)
        js1 = [js1[idx] for idx in range(nj1) if js1[idx]<=nit]
        #print js1
        tmp = [js1[idx+1]-js1[idx] for idx in range(nj1-1)]
        #print tmp
        #print 'nj =',nj1,'(failed :',js1[nj1-1]-nj1,')'
        ## Remove doublons
        # Index of non-doublons in js (if doublons, take the second one)
        jid = [idx for idx in range(nj1-1) if tmp[idx]>0] + [nj1-1]
        # Corrected list of runs numbers
        js = [js1[ix] for ix in jid]
        #print js
        #jid2 = [0] + [idx for idx in range(1,nj1) if tmp[idx-1]>0]
        #js2 = [js1[ix] for ix in jid2]
        #print js2
        nj = len(js)
        #print nj, len(js2)
        #if nj==len(js2):
            #print sum([abs(js2[ix]-js[ix]) for ix in range(nj)])
            #print ['('+str(jid2[ix])+','+str(jid[ix])+')' for ix in range(nj) if jid2[ix]!=jid[ix]]
        #jfail = [tmp[idx]-1 for idx in range(nj-1) if tmp[idx]>1]
        print 'nj =',nj,'(failed :',nit-nj,')'

        #sys.exit()

        f_par = tmppar+'/'+MCname+'_sampling_parameters.'+str(i)+'.txt'
        tmp_par = np.genfromtxt(f_par,delimiter=',')[::,1::]

        tmpdir2 = tmpdir+'/'+MCname+'_sampling.'+str(i)

        # Copy outputs from /users ?
        if docopy == 1:
            if len(glob.glob(tmpdir2))==0:
                os.system('mkdir '+tmpdir2)
            os.system('cp -p '+simdir+str(i)+'/*.tab '+tmpdir2+'/')

        # One summary file per job (might help adjusting memory space)
        if byjob == 1:
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_KGE2012.txt','w') as f_out:
                f_out.write('Iteration,'+','.join([x for x in obsnames])+'\n')
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_MAE.txt','w') as f_out:
                f_out.write('Iteration,'+','.join([x for x in obsnames])+'\n')
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_RMSE.txt','w') as f_out:
                f_out.write('Iteration,'+','.join([x for x in obsnames])+'\n')
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_corr.txt','w') as f_out:
                f_out.write('Iteration,'+','.join([x for x in obsnames])+'\n')
            # Parameters
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_parameters.txt','w') as f_out:
                f_out.write('Iteration,'+pnames+'\n')


        for iobs in range(nobs):

            f_sim = tmpdir2+'/'+simfiles[iobs]

            print obsnames[iobs],
            tmp = np.genfromtxt(f_sim,delimiter=',',skip_header=1)#,max_rows=nj)

            # initialize costfunction
            KGE[obsnames[iobs]] = [0]*nj
            MAE[obsnames[iobs]] = [0]*nj
            RMSE[obsnames[iobs]] = [0]*nj
            corr[obsnames[iobs]] = [0]*nj
            
            for j in range(1,nj+1):

                # -- Cost functions
                tmp2 = tmp[jid[j-1]]*simfct[iobs]

                # Crop between desired time frame, and account for potential gaps in the obs
                sim = [tmp2[idx+1] for idx in range(lsim) if any(obst[obsnames[iobs]]==simt[idx])==True]
                
                # Increment cost function              
                KGE[obsnames[iobs]][j-1] = metrics.kling_gupta(sim,obs[obsnames[iobs]],method='2012')
                MAE[obsnames[iobs]][j-1] = metrics.meanabs(sim,obs[obsnames[iobs]])
                RMSE[obsnames[iobs]][j-1] = metrics.rmse(sim,obs[obsnames[iobs]])
                corr[obsnames[iobs]][j-1] = metrics.corr(sim,obs[obsnames[iobs]])

                #print KGE[obsnames[iobs]][j-1]
                #print MAE[obsnames[iobs]][j-1]
                #print RMSE[obsnames[iobs]][j-1]
                #print corr[obsnames[iobs]][j-1]

                # A few prints
                #if j==1:
                    #print obsnames[iobs]
                    #print np.mean(sim), np.mean(np.ma.masked_array(obs[obsnames[iobs]],np.isnan(obs[obsnames[iobs]]))), len(sim), len(obs[obsnames[iobs]])
                    #print KGE[obsnames[iobs]][0], MAE[obsnames[iobs]][0], RMSE[obsnames[iobs]][0]
                
            if iobs ==0:
                # -- Parameters 
                #print j, js[j-1], idx, tmp_par.shape
                if byjob == 0:
                    with open(tmpdir+'/'+MCname+'_parameters.txt','a') as f_out:
                        for j in js:
                            f_out.write(str(i)+','+str(j)+','+str(itot)+','+','.join([str(x) for x in tmp_par[::,j-1]])+'\n')
                else:
                    with open(tmpdir+'/'+MCname+'_job'+str(i)+'_parameters.txt','a') as f_out:
                    #with open(tmpdir+'/'+MCname+'job_'+str(i)+'_parameters.txt','a') as f_out:
                        for j in js:
                            f_out.write(str(j)+','+','.join([str(x) for x in tmp_par[::,j-1]])+'\n')
                itot+=nj
        print       

        # Write over all jobs
        if byjob == 0:
            # KGE
            with open(tmpdir+'/'+MCname+'_KGE2012.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(','.join([str(i),str(js[j]),str(itot2),','.join([str(KGE[x][j]) for x in obsnames])])+'\n')
                    itot2+=1
            # MAE
            with open(tmpdir+'/'+MCname+'_MAE.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(','.join([str(i),str(js[j]),str(itot2),','.join([str(MAE[x][j]) for x in obsnames])])+'\n')
            # RMSE
            with open(tmpdir+'/'+MCname+'_RMSE.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(','.join([str(i),str(js[j]),str(itot2),','.join([str(RMSE[x][j]) for x in obsnames])])+'\n')
            # Correlation
            with open(tmpdir+'/'+MCname+'_corr.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(','.join([str(i),str(js[j]),str(itot2),','.join([str(corr[x][j]) for x in obsnames])])+'\n')

        # Job by job
        else:
            # KGE
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_KGE2012.txt','a') as f_out:
            #with open(tmpdir+'/'+MCname+'job_'+str(i)+'_KGE2012.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(str(js[j])+','+','.join([str(KGE[x][j]) for x in obsnames])+'\n')
            # MAE
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_MAE.txt','a') as f_out:
            #with open(tmpdir+'/'+MCname+'job_'+str(i)+'_MAE.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(str(js[j])+','+','.join([str(MAE[x][j]) for x in obsnames])+'\n')
            # RMSE
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_RMSE.txt','a') as f_out:
            #with open(tmpdir+'/'+MCname+'job_'+str(i)+'_RMSE.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(str(js[j])+','+','.join([str(RMSE[x][j]) for x in obsnames])+'\n')
            # Correlation
            with open(tmpdir+'/'+MCname+'_job'+str(i)+'_corr.txt','a') as f_out:
            #with open(tmpdir+'/'+MCname+'job_'+str(i)+'_corr.txt','a') as f_out:
                for j in range(nj):
                    f_out.write(str(js[j])+','+','.join([str(corr[x][j]) for x in obsnames])+'\n')

            # -- Copy to /users
            print 'Copy back to home base...'
            print
            os.system('cp -p '+tmpdir+'/'+MCname+'_job'+str(i)+'_*.txt '+os.getcwd()+'/'+outdir+'/')
            #os.system('cp -p '+tmpdir+'/'+MCname+'job_'+str(i)+'_*.txt '+os.getcwd()+'/'+outdir+'/')

            
            if clean == 1:
                print 'Cleaning up...'
                print
                os.system('rm -fr '+tmpdir2)


    if byjob == 0:
        print 'Number of complete samples:',itot, itot2
        print

        print 'Copy back to home base...'
        print
        os.system('cp -p '+tmpdir+'/'+MCname+'_*.txt '+os.getcwd()+'/'+outdir+'/')

        if clean == 1:
            print 'Cleaning up...'
            print
            for i in range(1,njob+1):
                tmpdir2 = tmpdir+'/'+MCname+'_sampling.'+str(i)
                os.system('rm -fr '+tmpdir2)

    print 'Done !'

