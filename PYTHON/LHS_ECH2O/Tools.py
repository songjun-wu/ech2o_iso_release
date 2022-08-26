#!/usr/bin/env python
# -*- coding: utf-8 -*-
# *************************************************
#
# Monte Carlo calibration algorithm for ECH2O
#
# -------
# Routine: Subroutines for parameters & obs manip & outputs
# -------
# Author: S. Kuppel
# Created on 10/2016
# -------------------------------------------------

from pcraster import *
import time, os, glob, sys, copy
import csv
from time import localtime, strftime
import numpy as np
from pyDOE import *

# ----------------------------------------------------------------------------
# -- Generate random set of parameters values of write it

def gen_paras(Opti, Config):

    #Opti.xtot = np.arange(1,Opti.nsamptot+1)

    # Latin Hypercube sampling
    
    # First, get the hypercube samples, ranging from 0 to 1
    mat = np.transpose(lhs(Opti.nvar,samples=Opti.nsamptot,criterion='m')) # Latin Hypercube Sampling of two variables, and 10 samples each.
        
    # Second, scale with the actual range
    for i in range(Opti.nvar):
        # Log transform where needed
        if Opti.log[i]==1:                
            tmp = 10**(mat[i]*np.log10(Opti.max[i]/Opti.min[i])+np.log(Opti.min[i]))
        else:
            tmp = mat[i]*(Opti.max[i]-Opti.min[i]) + Opti.min[i]
                
            
        if i==0:
            Opti.xtot = copy.copy(tmp)
        else:
            Opti.xtot = np.vstack((Opti.xtot,tmp))
                    
    #print i, Opti.names[i], Opti.x[i]

    # -- Reshape for output
    Opti.xtot = np.transpose(Opti.xtot)#.shape((Opti.nvar,Opti)

    # -- Write one file per parallel job
    for i in range(int(Config.ncpu)):
        f_out = Config.FILE_PAR+str(i+1)+'.txt'
        with open(f_out,'w') as fw:
            # fw.write('Sample,'+','.join(Opti.names)+'\n')
            fw.write(','.join(Opti.names)+'\n')
        for j in range(Opti.nit):
            k = i*Opti.nit + j
            with open(f_out,'a') as fw:
                #fw.write(str(j+1)+','+','.join([str(a) for a in Opti.xtot[k]])+'\n')
                fw.write(','.join([str(a) for a in Opti.xtot[k]])+'\n')

    # Write on file giving parameters range, log...(for later plots)
    f_out = Config.FILE_PAR+'char.txt'
    with open(f_out,'w') as fw:
        # fw.write('Sample,'+','.join(Opti.names)+'\n')
        fw.write('Names,'+','.join(Opti.names)+'\n')
        fw.write('Min,'+','.join([str(Opti.min[x]) for x in range(Opti.nvar)])+'\n')
        fw.write('Max,'+','.join([str(Opti.max[x]) for x in range(Opti.nvar)])+'\n')
        fw.write('Log,'+','.join([str(Opti.log[x]) for x in range(Opti.nvar)])+'\n')
    
    #np.savetxt(f_out,np.transpose(Opti.xtot))#,header= 

# ----------------------------------------------------------------------------
# -- Write parameters values file

def get_par(Opti,Config):
  
    # Open one file for all samples
    f_in = Config.FILE_PAR+Config.numsim+'.txt'
    print f_in
    Opti.xpar = np.genfromtxt(f_in,delimiter=',',skip_header=1)
    print Opti.xpar.shape

# ----------------------------------------------------------------------------
# -- Write parameters values file

def output_par(Opti,Config, it):
  
    # Open one file for all samples
    if Config.initpar==0:
        Config.f_par = Config.PATH_OUT+'/Parameters.txt'
        with open(Config.f_par,'w') as f_in:
            f_in.write('Iteration,'+','.join(Opti.names)+'\n')
        Config.initpar = 1

    with open(Config.f_par,'a') as f_in:
        f_in.write(str(it+1)+','+','.join([str(x) for x in Opti.x])+'\n')

# ----------------------------------------------------------------------------
# -- Updating inputs for ECH2O

def create_inputs(Opti, Paras, Site, Config, it):

    # Small switch not to read the vegetation params file every time
    readveg=1
    
    # -- Get the parameter sample of the current iteration
    Opti.x = Opti.xpar[it]

    for pname in Paras.names:

        #print pname

        ## - Mapped parameters
        if Paras.ref[pname]['veg']==0:

            # Soil unit dependence
            if Paras.ref[pname]['soil']==1 and pname!='Rootp.1' and pname!='Rootp.1+2':
                #print 'Soil dependent !!'
                outmap = Site.bmaps['unit']*0
                # Read each soil map unit and apply param value                
                for im in range(Site.ns):
                    outmap+= Site.bmaps[Site.soils[im]]*Opti.x[Paras.ind[pname][im]]

                report(outmap,Config.PATH_SPA+'/'+Paras.ref[pname]['file']+'.map')

            # No spatial/veg dependence, but channel stuff
            elif pname!='Rootp.1+2' and pname!='Rootp.1':
                #print 'Not dependent !!'
                if Paras.ref[pname]['file'] in ['chanwidth','chanmanningn']:
                    outmap = Site.bmaps['chanmask']*Opti.x[Paras.ind[pname]]
                elif Paras.ref[pname]['file'] == 'chanparam':
                    outmap = Site.bmaps['chanmask_NaN']*Opti.x[Paras.ind[pname]]
                else:
                    outmap = Site.bmaps['unit']*Opti.x[Paras.ind[pname]]

                report(outmap,Config.PATH_SPA+'/'+Paras.ref[pname]['file']+'.map')

            # Root layer 2: summed fraction over 1+2 minus fraction over 1
            elif pname=='Rootp.1':
                outmap = Site.bmaps['unit']*0
                outmap2 = Site.bmaps['unit']*0
                for im in range(Site.ns):
                    tmp = Opti.x[Paras.ind['Rootp.1'][im]]
                    outmap+= Site.bmaps[Site.soils[im]]*Opti.x[Paras.ind['Rootp.1+2'][im]]*tmp
                    outmap2+= Site.bmaps[Site.soils[im]]*Opti.x[Paras.ind['Rootp.1+2'][im]]*(1-tmp)
                #base = readmap(Config.PATH_SPA+'/unit.map')
                report(outmap, Config.PATH_SPA+'/rootfrac1.map')
                report(outmap2, Config.PATH_SPA+'/rootfrac2.map')
            
            # Outputs updated map

        
            # Check for initial condition/other parameter dependence
            # Initial soil water content
            if pname=='Porosity':
                report(outmap*0.8,Config.PATH_SPA+'/SWC1.map')
                report(outmap*0.8,Config.PATH_SPA+'/SWC2.map')
                report(outmap*0.8,Config.PATH_SPA+'/SWC3.map')        

        ## - Vegetation parameters
        else:
            # Change the value based on param name correspondance
            vegnew = copy.copy(Opti.vref)
            #print Opti.vref
            for iv in range(Site.nv):
                vegnew[iv][vegnew['name'].index(pname)] = str(Opti.x[Paras.ind[pname][iv]])

    # ------------------------------------------------------------------------------
    # Finalizing the preps....

        
    ## - Finalizing soil parameterization
    # Check that initial soil moisture is not smaller residual soil 
    # tbd... for now just pick the porosity and thetar reange wisely enough

    ## - Finalizing the vegetation parameterization
    if Paras.isveg > 0:
    # Equalize leaf turnover and additional turnover due to water and/or temperature stress
        #for iv in range(Site.nv):
        #    vegnew[iv][vegnew['name'].index('TurnovL_MWS')] = copy.copy(vegnew[iv][vegnew['name'].index('TurnovL')])
        #    vegnew[iv][vegnew['name'].index('TurnovL_MTS')] = copy.copy(vegnew[iv][vegnew['name'].index('TurnovL')])
    # Write the vegetation params file (if there's at least one veg param)
        vegfile = open(Config.PATH_SPA+'/'+Site.vfile,'w')
        vegfile.write('\t'.join(Opti.vref['header'])+'\n')
        for iv in range(Site.nv):
            vegfile.write('\t'.join(vegnew[iv]) +'\n')
        vegfile.write('\t'.join(Opti.vref['footer'])+'\n')
        vegfile.write('\t'.join(Opti.vref['name'])+'\n')
        vegfile.close()

# ----------------------------------------------------------------------------
# -- Check is ECH2O ran properly

def runOK(Data, Opti, Config):

    isOK = 0

    # 1. Check it ran
    f_test1 = Config.PATH_EXEC+'/BasinSummary.txt'
    f_test2 = Config.PATH_EXEC+'/'+Data.obs[Data.names[0]]['sim_file']
    if len(glob.glob(f_test1))*len(glob.glob(f_test2))!=0:
        #print 'Outputs are there...'

        # 2. Check it ran until the end
        #tmp1 = np.genfromtxt(f_test1,skip_header=1,unpack=True)[0]
        tmp2 = np.genfromtxt(f_test2,skip_header=Data.nts+3,unpack=True)[0]
        if type(tmp2)!=float and type(tmp2)!=np.float64 and type(tmp2)!=np.float32:
            if len(tmp2)==Data.lsim: # & len(tmp2)==Data.lsim:
                # print 'It ran until the end !'
                isOK = 1

    return isOK
        
# ----------------------------------------------------------------------------
# -- Manage outputs        

def manage_outputs(Data, Opti, Config, it):

    # -- Group the output files in one across simulations, 
    #    separating by observations points and veg type where it applies

    # Initialization
    if Config.initobs == 0:
        # Basin summary
        Config.f_bs = Config.PATH_EXEC+'/BasinSummary.txt'
        Opti.f_bs_hist = Config.PATH_OUT+'/BasinSummary_hist.txt'
        # Header of files
        with open(Config.f_bs,'r') as f_in:
            tmp = f_in.readline()
            with open(Opti.f_bs_hist,'w') as f_out:
                f_out.write('Iteration,'+','.join(tmp.split('\t')))

        for oname in Data.names:
            # Historic time series file names
            Data.obs[oname]['sim_hist'] = Config.PATH_OUT+'/'+oname+'_hist.tab'
            # Header of files
            with open(Data.obs[oname]['sim_hist'],'w') as f_out:
                f_out.write('Iteration,'+','.join([str(it+1) for i in range(Data.lsim)])+'\n')

        Config.initobs = 1

    # Save current run outputs (and delete the file to relieve Maxwell...)
    # Summary: last line
    tmp = np.genfromtxt(Config.f_bs,skip_header=Data.lsim)
    with open(Opti.f_bs_hist,'a') as f_out:
        f_out.write(str(it+1)+','+','.join([str(i+1) for i in list(tmp)])+'\n')

    # Time series
    for oname in Data.names:
        #print oname,
        if oname == 'SaturationArea':
            hskip = 1
            idx = Data.obs[oname]['sim_pts']-1
        else:
            hskip = Data.nts+3
            idx = np.argsort(np.array(Data.sim_order))[Data.obs[oname]['sim_pts']-1]+1
        #print hskip, idx

        tmp = np.genfromtxt(Data.obs[oname]['sim_file'],delimiter='\t',
                            skip_header=hskip,unpack=True)[idx]

        with open(Data.obs[oname]['sim_hist'],'a') as f_out:
                f_out.write(str(it+1)+','+','.join([str(j) for j in list(tmp)])+'\n')
