from FoM import FoM

PLOT_PATH = "/global/cfs/cdirs/lsst/groups/TD/SN/SNANA/SURVEYS/LSST/USERS/kessler/debug/submit_batch_firecrown/NEW_AYAN_DEBUG-3/FIRECROWN_OUTPUT/PLOTS"
stream = "~/trash/covmat.txt"

#FoM(stream)
print(int(FoM(PLOT_PATH+'/covmat.txt')))
