Ayan Mitra 2023

https://github.com/am610/Firecrown_wrapper_TD

# **Firecrown Wrapper Manual for running with Cosmosis for SN Cosmology**



## **Summary** 

The Firecrown wrapper is a standalone script which links a Supernova input
data file to Cosmosis for dark energy parameter estimation via firecrown
likelihood module. <p style='color:red'>*The wrapper can be used in any system, provided* `Firecrown` *and* `Cosmosis` *are installed in the environment. However, the current version of the* README *is mostly focused on, use in* NERSC Perlmutter LSST DESC *environment.*</p>

## **Why** 

Firecrown runs in 3 stages, including a data-prep stage into sacc [1] format.
The firecrown wrapper executes these 3 stages as a single task, making
firecrown easier to use and easier to embed in pipelines.

## **Firecrown Wrapper Flowchart** 

 SN Hubble Diagram (HD) + Covariance Matrix [Input]
 --> Single `sacc` file
     --> Firecrown Likelihood
          --> Cosmosis
	       --> DE Parameter estimation
	           --> Plots [Output]


## **Input requirements** 

#### Mandatory  :

(1) Input file path to HD and covariance matrix,

(2)  Name of HD file and covariance matrix file,

(3) cosmosis input
	 `ini` file.

Assumption : HD and covariance matrix files are
	 in the same folder.

Additional optional attributes
	 can be seen (in Perlmutter) via the following help command : 
	 `$TD/SOFTWARE/firecrown_wrapper/dist/Firecrown_wrapper
	 --help`

#### ENV Requirement : 
(a) **Perlmutter** :The TD ENV should be active

`source /global/cfs/cdirs/lsst/groups/TD/setup_td.sh`

(b) **Chicago-RCC** : 

(c) **FNAL**  :
   


## **Installation**		

	  git clone https://github.com/am610/Firecrown_wrapper_TD.git
	  cd Firecrown_wrapper_TD/
   	  pyinstaller Firecrown_wrapper.spec
	  
This will create the executable version of the wrapper. If `pyinstaller` is not present, install using `pip` [2].   

### **Notes** 

The wrapper can be used :

(a) with `SNANA` or `DESC
TD` pipeline's utility function : `submit_batch_jobs.sh` for
submitting multiple batch job(s).

(b) or also as a standalone unit for submitting
batch job in Perlmutter using `sbatch`.



## **Syntax** (Perlmutter Specific)

(a) To run with `submit_batch_jobs.sh` a separate Input yaml
	 file is needed suitable for `submit_batch_jobs.sh`. An example
	 of a test.yaml is below :


	  ## YAML begins :
	  CONFIG:
	    BATCH_INFO: sbatch
	    $SBATCH_TEMPLATES/SBATCH_Perlmutter.TEMPLATE 25
	    JOBNAME: srun -n 2 $TD/SOFTWARE/firecrown_wrapper/dist/Firecrown_wrapper
	    BATCH_WALLTIME: "12:00:00" FIRECROWN_INPUT_FILE:
	    /global/cfs/cdirs/lsst/groups/TD/SN/SNANA/SURVEYS/LSST/ROOT/starterKits/firecrown+submit_batch_jobs/Cosmosis_Input_Scripts/sn_planck.ini
	    ENV_REQUIRE: FIRECROWN_DIR FIRECROWN_EXAMPLES_DIR CSL_DIR
	    OUTDIR: output_firecrown_sn_cmb WFITAVG:
	    - LSST_BINNED_COV_BBC_SIMDATA_PHOTOZ
	    COVOPT:  ALL NOSYS INPDIR: -
	    /pscratch/sd/d/desctd/PIPPIN_OUTPUT/PLASTICC_COMBINED_PUBLISHED/7_CREATE_COV/LSST_BINNED_COV_BBC_SIMDATA_PHOTOZ_1/output
	    -
	    /pscratch/sd/d/desctd/PIPPIN_OUTPUT/PLASTICC_COMBINED_PUBLISHED/7_CREATE_COV/LSST_BINNED_COV_BBC_SIMDATA_PHOTOZ_2/output
	  ##END_YAML


Launch the job : `submit_batch_jobs.sh test.yaml`

*** **In NERSC Perlmutter, a starter kit is available with example inputs in** :
	 `/global/cfs/cdirs/lsst/groups/TD/SN/SNANA/SURVEYS/LSST/ROOT/starterKits/firecrown+submit_batch_jobs`


(b) To simply run the code as a batch job in Perlmutter the
	 following example job script can be used as a template :

	  #!/bin/bash
	  #SBATCH -A m1727
	  #SBATCH -C cpu
	  #SBATCH --qos=debug
	  #SBATCH --time=00:10:00
	  #SBATCH --nodes=2
	  #SBATCH --error=perl_firecrown-%j.err
	  #SBATCH -o perl_firecrown.log
	  #SBATCH --mail-user=ayanmitra375@gmail.com
	  #SBATCH -J Firecrown


	  NUM_PROCESSES=32
	  export OMP_NUM_THREADS=16

	  #Example 1
	  # Syntax : srun -u -n ${NUM_PROCESSES}  --cpus-per-task ${OMP_NUM_THREADS} $TD/SOFTWARE/firecrown_wrapper/dist/Firecrown_wrapper [Input/Folder/HD/covariance/matrix] [HD.txt] [cov.txt] [cosmosis.ini]
	  srun -u -n ${NUM_PROCESSES}  --cpus-per-task ${OMP_NUM_THREADS} $TD/SOFTWARE/firecrown_wrapper/dist/Firecrown_wrapper $HOME/Analysis/7_CREATE_COV/LSST_BINNED_COV_BBC_SIMDATA_PHOTOZ_1/output hubble_diagram.txt covsys_000.txt.gz sn_only.ini --summary $PWD/FIRECROWN_OUTPUT/SUMMARY.YAML -O $PWD/FIRECROWN_OUTPUT/

	  # ## End of file

Save the above code in a file `test.sh` and then from Perlmutter terminal submit the job as : `sbatch test.sh`


*Notes : qos = `debug` can be changed to `regular`. `nodes`
and time can be modified accordingly (as of now Perlmutter's
maximum time limit is 12 hours). The outputs will be stored
in `$PWD/FIRECROWN_OUTPUT/`. cosmosis input file shown here is
`sn_only.ini`, consult cosmosis manual for more information.
`ini` file should be at the same location as job script.

Example of `lsst_srd_y10` are kept in : 
`/global/cfs/cdirs/lsst/groups/TD/SN/SNANA/SURVEYS/LSST/ROOT/starterKits/firecrown+sbatch/`

## **Compiling** ---------[**For Developers**]

For regular use in Perlmutter it is not needed to be compiled. Developers can follow as below:

	  cd <firecrown_wrapper location>
	  pyinstaller --onefile Firecrown_wrapper.py

if you get pyinstaller error then, add the following lines in the `Firecrown_wrapper.spec` file :

	  import sys ;
	  sys.setrecursionlimit(sys.getrecursionlimit() * 5)
then run the following again :

	  pyinstaller  Firecrown_wrapper.spec


## **Outputs** 

Each successful output will produce the following three
	 sub folders in the desired location :
	 
	 (1) COSMOSIS-CHAINS
	     Contains the output chain files (name as written in input
	     `.ini` file) and `INPUT.INFO` file which logs all input
	     commands.

	 (2) ERROR_LOGS
	     contains the error and log files of each stages. Also
	     contains files recording the time taken in each stages.

	 (3) PLOTS
	     contains the results of the analysis from the chain files
	     i.e. plots and parameter estimation summary files.


	 (4) Summary Yaml file : summarizes the outcomes of each stages
	 : Fail or Successful. Also lists the main cosmological results
	 (some fields are still under construction).


## **Example Runtimes** 

         Running the example `sn_planck.ini` for emcee smapler with nsteps = 10, samples = 100,walkers = 24, etc. using submit_batch_jobs.sh
	 for different number of cores and N (= MPI tasks) specification
	 
         Core  N. Time
         20.   3.  4.755 hrs
         25.   1.  2.142
         25    2.  1.964 
         40    1   1.810
	 
********************************************************************
********************************************************************


[1] https://sacc.readthedocs.io/en/latest/intro.html

[2] https://pyinstaller.org/en/stable/installation.html
