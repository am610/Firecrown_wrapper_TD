"""
Example Input :
python Firecrown_wrapper.py /global/homes/a/ayanmitr/Analysis/7_CREATE_COV/LSST_BINNED_COV_BBC_SIMDATA_PHOTOZ_1/output hubble_diagram.txt covsys_000.txt.gz sn_only.ini -O $HOME/trash -p "omega_m = 0.3"


$TD_SOFTWARE/firecrown_wrapper/dist/Firecrown_wrapper /global/homes/a/ayanmitr/Analysis/7_CREATE_COV/LSST_BINNED_COV_BBC_SIMDATA_PHOTOZ_1/output hubble_diagram.txt covsys_000.txt.gz sn_only.ini
"""

import pandas as pd
import numpy as np
import os
import sys
import yaml
import signal
import subprocess
from subprocess import Popen
import datetime
import logging
import warnings
import time
import argparse
import pathlib
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, RawTextHelpFormatter
from contextlib import contextmanager
import textwrap
from FoM import FoM

# import CHISQ

logging.basicConfig(level=logging.INFO)
with warnings.catch_warnings():
    warnings.simplefilter("ignore")


@contextmanager
# https://stackoverflow.com/questions/7152762/how-to-redirect-print-output-to-a-file
def redirected_stdout(outstream):
    orig_stdout = sys.stdout
    try:
        sys.stdout = outstream
        yield
    finally:
        sys.stdout = orig_stdout


# Setting up the 'yaml' file
class CustomHelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
    def _split_lines(self, text, width):
        wrapper = textwrap.TextWrapper(width=width)
        lines = []
        for line in text.splitlines():
            if len(line) > width:
                lines.extend(wrapper.wrap(line))
            else:
                lines.append(line)
        return lines


time0 = time.time()
now = datetime.datetime.now()
print("Current Time = ", now)
dt_string = now.strftime("%d%m%Y_%H%M%S/")
ENV = os.environ["SNANA_DEBUG"]
OUTPUT_PATH = os.path.join(
    ENV, "submit_batch_firecrown/NEW_AYAN_DEBUG-3/FIRECROWN_OUTPUT/"
)

usage = "Mandatory arguments required in  fixed order"
# parser = argparse.ArgumentParser(formatter_class=CustomHelpFormatter, description=usage)
parser = argparse.ArgumentParser(description=usage)
parser.add_argument("path", help="Path for the HD and COV")
parser.add_argument("hd", help="HD ")
parser.add_argument("cov", help="COV ")
parser.add_argument("ini", help="*.ini file")
parser.add_argument(
    "-O",
    "--outdir",
    type=pathlib.Path,
    default=OUTPUT_PATH,
    help="-O Output path (Default: %s)" % (OUTPUT_PATH),
)
parser.add_argument(
    "-p",
    "--param",
    #    action='store_true',
    default="",
    nargs="?",
    help="-p Override cosmosis parameter values ",
)
parser.add_argument(
    "-s",
    "--summary",
    type=pathlib.Path,
    default=os.path.join(OUTPUT_PATH, "SUMMARY.YAML"),
    help="-s SUMMARY.YAML output path (Default: %s)" % (OUTPUT_PATH),
)
"""
parser.add_argument(
    "-i",
    "--info",
    type=pathlib.Path,
    default=COSMOSIS_PATH + "INPUT.INFO",
    help="-i INPUT.INFO output path (Default: %s)" % (OUTPUT_PATH),
)
"""
args = parser.parse_args()

SUBDIRER = "/ERROR_LOGS/"
SUBDIR3 = "/COSMOSIS-CHAINS/"
SUBDIR4 = "/PLOTS"
OUTPUT_PATH = os.path.expandvars(args.outdir)
SUMMARY_PATH = os.path.expandvars(args.summary)
# SUBMIT_PATH = os.path.expandvars(args.info)
ERROR_PATH = os.path.expandvars(OUTPUT_PATH + SUBDIRER)
COSMOSIS_PATH = os.path.expandvars(OUTPUT_PATH + SUBDIR3)
PLOT_PATH = os.path.expandvars(OUTPUT_PATH + SUBDIR4)
try:
    os.makedirs(COSMOSIS_PATH)
except FileExistsError:
    # directory already exists
    pass
SUBMIT_PATH = COSMOSIS_PATH + "INPUT.INFO"
p = args.param

with open(r"%s" % (SUBMIT_PATH), "w", buffering=1) as OF:
    with redirected_stdout(OF):
        print(
            "\n\nSTAGE 0 = ALL PATH AND FILES IN ARGUMENTS CHECK\nSTAGE 1 = 'generate_sn_data.py'\nSTAGE 2 = COSMOSIS\nSTAGE 3 = POST PROCESSING (PLOT)\n\n"
        )

    Key = [
        "STAGE0",
        "STAGE1",
        "STAGE2",
        "STAGE3",
        "ABORT_IF_ZERO",
        "FoM",
        "Ndof",
        "CPU_MINUTES",
        "chi2",
        "sigint",
        "label",
        "BLIND",
        "NWARNINGS",
        "w0",
        "w0sig_marg",
        "wa",
        "wasig_marg",
        "OM",
        "OMsig_marg",
        "w0ran",
        "waran",
        "OMran",
    ]
    data = {}
    # -------------------------------

    # Function Defintions

    # key set to non abort(0) case, guide for sbatch
    def path_error(path):
        if os.path.exists(path):
            data[Key[4]] = 1
            pass
        else:
            data[Key[0]] = "FAILED"
            data[Key[4]] = 0
            outputs = yaml.dump(data, file_yaml)
            raise FileNotFoundError("{0} path does not exist!".format(path))

    def file_error(file):
        if os.path.isfile(file):
            data[Key[4]] = 1
            pass
        else:
            data[Key[0]] = "FAILED"
            data[Key[4]] = 0
            outputs = yaml.dump(data, file_yaml)
            raise FileNotFoundError("{0} file does not exist!".format(file))

    def burnin(chain):
        a = pd.read_csv(chain, comment="#", header=None, sep="\s+")
        L = int(0.15 * int(np.shape(a)[0]))
        return L

    # ----------------------------

    """
        Creating output folders
    """
    if not os.path.exists(ERROR_PATH):
        os.makedirs(ERROR_PATH, exist_ok=True)
    if not os.path.exists(COSMOSIS_PATH):
        os.makedirs(COSMOSIS_PATH, exist_ok=True)
    if not os.path.exists(PLOT_PATH):
        os.makedirs(PLOT_PATH, exist_ok=True)

    """
    Checking Files exists
    """
    with open(r"%s" % (SUMMARY_PATH), "w", buffering=1) as file_yaml:
        with redirected_stdout(OF):
            print("\n#Required Info")
            print("CWR:", os.getcwd())
            print("ARG_LIST:", sys.argv)
            print("TIME_STAMP:", now.strftime("%d-%m-%Y %H:%M:%S"))
            print("OUTPUT DIR:", OUTPUT_PATH, "\n")

        PWD = os.getcwd()
        # arg_error(len(sys.argv))
        path = args.path
        hd = args.hd
        cov = args.cov
        ini = os.path.split(args.ini)[1]
        # ini_f= args.ini
        path_error(path)
        f1 = os.path.join(path, hd)
        file_error(f1)
        f2 = os.path.join(path, cov)
        file_error(f2)
        data[Key[0]] = "SUCCESS"
        # ********************
        # --------------------
        HD_read = pd.read_csv(f1, comment="#", sep=r"\s+")
        sacc_path_rm = "rm " + os.path.join(PWD, "srd-y1-converted.sacc")
        job0 = subprocess.Popen(sacc_path_rm, stdout=subprocess.PIPE, shell=True)

        # Stage 1
        # python $FIRECROWN_EXAMPLES_DIR/srd_sn/generate_sn_data.py ${path} ${HD} ${COV}
        # This assumes that the output  will be a `sacc' file which
        # will be automatically read in by cosmosis input `ini' file.
        startTime = time.time()
        os.environ["PYTHONUNBUFFERED"] = "1"
        Vector = path + " " + hd + " " + cov
        with redirected_stdout(OF):
            print("SACC Input Vector:", Vector)
        with open(
            "%sgenerate_sn_data_output_%s.log" % (ERROR_PATH, ini), "wb"
        ) as gen_file, open(
            "%sgenerate_sn_data_output_ERROR_%s.err" % (ERROR_PATH, ini), "wb"
        ) as gen_file_e:
            job1 = Popen(
                "python "
                + "$FIRECROWN_EXAMPLES_DIR/srd_sn/generate_sn_data.py "
                + Vector,
                shell=True,
                text=True,
                stdout=gen_file,
                stderr=gen_file_e,
            )
        job1.wait()
        file = open("%sgenerate_sn_data_output_%s.log" % (ERROR_PATH, ini), "a")
        sys.stdout = file
        with redirected_stdout(OF):
            print(job1.stdout)
        file_e = open("%sgenerate_sn_data_output_ERROR_%s.err" % (ERROR_PATH, ini), "a")
        sys.stdout = file_e
        with redirected_stdout(OF):
            print(job1.stderr)
        if job1.returncode != 0:
            os.system('echo "STAGE 1 FAILED *** \nCheck generate_sn_data error logs"')
            data[Key[1]] = "FAILED"
            data[Key[4]] = 0
            outputs = yaml.dump(data, file_yaml)
            executionTime = np.array(round((time.time() - startTime), 2))
            with open("%sTimer_STAGE_1.time" % (ERROR_PATH), "w") as f:
                f.write("%s" % executionTime)
            sys.exit("BYE")
        else:
            data[Key[1]] = "SUCCESS"
            data[Key[4]] = 1
            executionTime = np.array(round((time.time() - startTime), 2))
            with open("%sTimer_STAGE_1.time" % (ERROR_PATH), "w") as f:
                f.write("%s" % executionTime)

            os.system('echo "STAGE 1 COMPLETE"')

        ## STAGE 2
        ## python $FIRECROWN_EXAMPLES_DIR/srd_sn/sn_srd.py ${INPUT}
        ## input_SN_sacc_file.sacc
        sacc_path_cp = "cp " + os.path.join(
            PWD, "srd-y1-converted.sacc $FIRECROWN_EXAMPLES_DIR/srd_sn/"
        )
        job2 = subprocess.Popen(
            sacc_path_cp,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        job2.wait()
        # STAGE 3
        # srun -n 16 --cpu-bind=cores -c 16  cosmosis   sn_only.ini -p omega_m = 0.3
        startTime = time.time()
        jobname = "cosmosis"
        arg = "-p "
        arg2 = "output.filename="
        Vector = (
            " "
            + ini
            + " "
            + arg
            + arg2
            + COSMOSIS_PATH
            + os.path.splitext(ini)[0]
            + ".txt  --mpi"
        )
        with redirected_stdout(OF):
            print("Cosmosis Input Vector:", Vector)
        with open("%sCOSMOSIS_output_%s.log" % (ERROR_PATH, ini), "wb") as file, open(
            "%sCOSMOSIS_output_ERROR_%s.err" % (ERROR_PATH, ini), "wb"
        ) as file_e:
            job3 = subprocess.Popen(
                ["cosmosis" + Vector],
                shell=True,
                text=True,
                stdout=file,
                stderr=file_e,
            )
        job3.wait()
        if job3.returncode != 0:
            os.system('echo "STAGE 2 FAILED *** \nCheck COSMOSIS error logs"')
            data[Key[2]] = "FAILED"
            data[Key[4]] = 0
            outputs = yaml.dump(data, file_yaml)
            executionTime = np.array(round((time.time() - startTime), 2))
            with open("%sTimer_COSMOSIS.time" % (ERROR_PATH), "w") as f:
                f.write("%s" % executionTime)
            sys.exit("BYE")
        else:
            data[Key[2]] = "SUCCESS"
            data[Key[4]] = 1
            executionTime = np.array(round((time.time() - startTime), 2))
            with open("%sTimer_COSMOSIS.time" % (ERROR_PATH), "w") as f:
                f.write("%s" % executionTime)
            os.system('echo "STAGE 2 COMPLETE"')

        # STAGE 4
        # cosmosis-postprocess ${ini} # -o OUTDIR
        startTime = time.time()
        jobname = "cosmosis-postprocess"
        arg = " -o "
        burnpath = os.path.join(COSMOSIS_PATH, str(ini.replace(".ini", ".txt")))
        burn = " --burn " + str(burnin(burnpath)) + " "  # 15% burnin
        Vector = (
            " "
            + COSMOSIS_PATH
            + ini.replace(".ini", "*.txt")
            + arg
            + PLOT_PATH
            + str(burn)
        )
        with redirected_stdout(OF):
            print("cosmosis-postprocess Input Vector:", Vector)
        with open(
            "%sPostProcess_output_%s.log" % (ERROR_PATH, ini), "wb"
        ) as file_post, open(
            "%sPostProcess_output_ERROR_%s.err" % (ERROR_PATH, ini), "wb"
        ) as file_post_e:
            job4 = subprocess.Popen(
                jobname + Vector,
                shell=True,
                text=True,
                stdout=file_post,
                stderr=file_post_e,
            )
        job4.wait()
        if job4.returncode != 0:
            os.system('echo "STAGE 3 FAILED *** \nCheck PostProcess error logs"')
            data[Key[3]] = "FAILED"
            data[Key[4]] = 0
            outputs = yaml.dump(data, file_yaml)
            executionTime = np.array(round((time.time() - startTime), 2))
            with open("%sTimer_PostProcess.time" % (ERROR_PATH), "w") as f:
                f.write("%s" % executionTime)
            sys.exit("BYE")
        else:
            data[Key[3]] = "SUCCESS"
            data[Key[4]] = 1
            # Attributes will be printed only in this (last) stage
            # "XXX"
            cosmo_params = pd.read_csv(
                os.path.join(PLOT_PATH, "means.txt"),
                sep=r"\s+",
                comment="#",
                header=None,
            ).T
            cosmo_params = cosmo_params.T.set_index(0).T
            data["FoM"] = int(FoM(os.path.join(PLOT_PATH, "covmat.txt")))
            data["Ndof"] = np.shape(HD_read)[0]
            data["CPU_MINUTES"] = round((time.time() - time0) / 60, 2)  # in minutes
            data["chi2"] = 22  # round(float(CHISQ.ch(COSMOSIS_PATH,ini)),3)  #22
            data["sigint"] = 0.0
            data["label"] = "none"
            data["BLIND"] = 0
            data["NWARNINGS"] = 1
            data["w0"] = cosmo_params["cosmological_parameters--w"].iloc[0]
            data["w0sig_marg"] = cosmo_params["cosmological_parameters--w"].iloc[1]
            data["wa"] = cosmo_params["cosmological_parameters--wa"].iloc[0]
            data["wasig_marg"] = cosmo_params["cosmological_parameters--wa"].iloc[1]
            data["OM"] = cosmo_params["cosmological_parameters--omega_m"].iloc[0]
            data["OMsig_marg"] = cosmo_params["cosmological_parameters--omega_m"].iloc[
                1
            ]
            data["w0ran"] = 0
            data["waran"] = 0
            data["OMran"] = 0
            # "XXX"
            # """
            os.system('echo "STAGE 3 COMPLETE"')
            os.system('echo "ALL DONE"')
            outputs = yaml.dump(data, file_yaml)
            executionTime = np.array(round((time.time() - startTime), 2))
            with open("%sTimer_PostProcess.time" % (ERROR_PATH), "w") as f:
                f.write("%s" % executionTime)
            # print(outputs)
