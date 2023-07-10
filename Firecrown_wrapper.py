"""
Firecrown Wrapper
@ Ayan Mitra 2023

This script automates the process of generating Supernovae data, running a
cosmological analysis with COSMOSIS, and post-processing the results. It takes
as input the paths to the HD and COV files, an ini file, and optional paths
for the output directory and a SUMMARY.YAML file, along with optional COSMOSIS
parameter overrides.

Usage:
    python firecrown_wrapper.py <path> <hd> <cov> <ini> [-O <outdir>] [-p <param>] [-s <summary>]

Where:
    <path> is the path for the HD and COV files.
    <hd> is the HD file.
    <cov> is the COV file.
    <ini> is the *.ini file.
    <outdir> (optional) is the output path (default is './').
    <param> (optional) is a string to override COSMOSIS parameter values.
    <summary> (optional) is the SUMMARY.YAML output path (default is './SUMMARY.YAML').

This script has been structured into several functions for modularity and readability:
    parse_arguments() - Parses and validates command-line arguments.
    setup_directories() - Sets up the necessary output directories.
    redirect_stdout() - Redirects stdout to a specified stream.
    run_subprocess() - Runs a command in a subprocess, handling output and errors.
    check_files_and_paths() - Checks if specified files and directories exist.
    run_stages() - Runs the various stages of the analysis.
    burnin() - Calculates the burn-in length for a MCMC chain.
    main() - The main function that calls all the above functions in sequence.
"""


import argparse
import os
import pathlib
import subprocess
import sys
import queue
import threading
import time
import traceback
import numpy as np
import pandas as pd
import yaml
import logging
import itertools
#from mpi4py import MPI
from contextlib import contextmanager
time0 = time.time()

# Initialize logger
logging.basicConfig(filename='wrapper.log', level=logging.INFO)

OUTPUT_PATH = os.getcwd()

summary = {
    "STAGE0": "NOT_STARTED",
    "STAGE1": "NOT_STARTED",
    "STAGE2": "NOT_STARTED",
    "STAGE3": "NOT_STARTED",
    "ABORT_IF_ZERO": 1,
    "FoM": None,
    "Ndof": None,
    "CPU_MINUTES": None,
    "chi2": None,
    "sigint": None,
    "label": None,
    "BLIND": None,
    "NWARNINGS": None,
    "w0": None,
    "w0sig_marg": None,
    "wa": None,
    "wasig_marg": None,
    "OM": None,
    "OMsig_marg": None,
    "w0ran": None,
    "waran": None,
    "OMran": None,
}

def write_summary():
    with open('SUMMARY.YAML', 'w') as f:
        yaml.dump(summary, f)

@contextmanager
def redirect_stdout(out_file):
    """Redirects stdout to the provided file."""
    orig_stdout = sys.stdout
    try:
        sys.stdout = out_file
        yield
    finally:
        sys.stdout = orig_stdout

def valid_directory_path(string):
    if not os.path.isdir(string):
        #raise argparse.ArgumentTypeError(f"{string} is not a valid directory path")
        os.makedirs(string, exist_ok=True)
    return string
        
def parse_arguments():
    """Parse and validate command-line arguments."""
    usage = "Mandatory arguments required in fixed order"
    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument("path", help="Path for the HD and COV", type=valid_directory_path)
    parser.add_argument("hd", help="HD")
    parser.add_argument("cov", help="COV")
    parser.add_argument("ini", help="*.ini file")
    parser.add_argument(
        "-O",
        "--outdir",
        type=valid_directory_path,
        default=OUTPUT_PATH,
        help="-O Output path (Default: %s)" % (OUTPUT_PATH),
    )
    parser.add_argument(
        "-p",
        "--param",
        default="",
        nargs="?",
        help="-p Override COSMOSIS parameter values",
    )
    parser.add_argument(
        "-s",
        "--summary",
        type=pathlib.Path,
        default=os.path.join(OUTPUT_PATH, "SUMMARY.YAML"),
        help="-s SUMMARY.YAML output path (Default: %s)" % (OUTPUT_PATH),
    )
    args = parser.parse_args()
    return args


def setup_directories(output_path):
    """Create necessary directories."""
    subdirs = ["ERROR_LOGS", "COSMOSIS-CHAINS", "PLOTS"]
    for subdir in subdirs:
        # Create the full path                                                                                                                                          
        dir_path = os.path.join(output_path, subdir)
        try:
            os.makedirs(dir_path, exist_ok=True)
        except FileExistsError:
            pass  # Directory already exists


def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def run_subprocess(command, output_file, error_file):
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    q_stdout = queue.Queue()
    q_stderr = queue.Queue()

    t_stdout = threading.Thread(target=enqueue_output, args=(process.stdout, q_stdout))
    t_stdout.daemon = True
    t_stdout.start()

    t_stderr = threading.Thread(target=enqueue_output, args=(process.stderr, q_stderr))
    t_stderr.daemon = True
    t_stderr.start()

    """Run a command in a subprocess, handling output and errors."""

    with open(output_file, "wb") as out_file, open(error_file, "wb") as err_file:
        while process.poll() is None:
            while not q_stdout.empty():
                out_file.write(q_stdout.get())
            while not q_stderr.empty():
                err_file.write(q_stderr.get())
            time.sleep(0.1)

    return process.returncode
        

'''        
def run_subprocess(command, output_file, error_file):
    with open(output_file, "wb") as out_file, open(error_file, "wb") as err_file:
        process = subprocess.Popen(
            command,
            shell=True,
            text=True,
            stdout=out_file,
            stderr=err_file,
        )
        process.wait()
    return process.returncode
'''

def check_files_and_paths(files, dir_paths):
    """Check if the specified files and directories exist."""
    for dir_path in dir_paths:
        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"{dir_path} does not exist!")
        for file in files:
            if not os.path.isfile(os.path.join(dir_path, file)):
                raise FileNotFoundError(f"{file} does not exist in the given location!")



def FoM(input_file):
    """
    Calculate the Dark Energy Figure of Merit (FoM) for a given covariance matrix.

    The FoM is defined as the inverse of the square root of the determinant of the covariance matrix.

    Parameters
    ----------
    input_file : str
        The path to the input file containing the covariance matrix.

    Returns
    -------
    FoM : float
        The Figure of Merit.
    """
    a = pd.read_csv(input_file, sep=r"\s+")
    mat = np.asarray(a)
    names = ["cosmological_parameters--w", "cosmological_parameters--wa"]
    ind = []
    FoM_COV = []
    for n in list(a):
        if n == names[0] or n == names[1]:
            N = list(a).index(n)
            ind.append(N)
    cov = list(itertools.product(ind, repeat=2))
    for i in cov:
        tmp = mat[i]
        FoM_COV.append(tmp)
    FoM_COV = np.reshape(FoM_COV, (2, 2))
    X = np.linalg.det(FoM_COV)
    FoM = 1 / np.sqrt(X)
    return FoM


def burnin(chain: str) -> int:
    """
    Calculate the burn-in length for a MCMC chain.

    Parameters
    ----------
    chain : str
        The path to the MCMC chain file.

    Returns
    -------
    int
        The burn-in length, calculated as 15% of the number of steps in the chain.
    """
    try:
        a = pd.read_csv(chain, comment="#", header=None, sep=r"\s+")
        L = int(0.15 * a.shape[0])
        return L
    except FileNotFoundError:
        print(f"File not found: {chain}", file=sys.stderr)
        raise


def run_stages(path, hd, cov, ini, error_path, output_path, plot_path):
    """Run the various stages of the analysis."""

    # Get the rank of the current MPI process
    # rank = MPI.COMM_WORLD.Get_rank()

    # List to store the commands
    commands = []
    
    # Stage 1
    summary["STAGE0"] = "STARTED"
    write_summary()

    # Remove any preexisting sacc file
    PWD = os.getcwd()
    sacc_path_rm = "rm " + os.path.join(PWD, "srd-y1-converted.sacc")
    job0 = subprocess.Popen(sacc_path_rm, stdout=subprocess.PIPE, shell=True)
    stdout, stderr = job0.communicate()

    stage_1_command = f"python $FIRECROWN_EXAMPLES_DIR/srd_sn/generate_sn_data.py {path} {hd} {cov}"
    commands.append(f"\n SACC Input Vector: {stage_1_command} \n")
    returncode = run_subprocess(stage_1_command, f"{error_path}/generate_sn_data_output_{ini}.log", f"{error_path}/generate_sn_data_output_ERROR_{ini}.err")
    if returncode != 0:
        summary["STAGE0"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
#            with open(os.path.join(error_path, 'INPUT.INFO'), 'a') as f:
#                f.write(f"SACC Input Vector: {stage_1_command}\n")
        raise RuntimeError("Stage 1 failed. Check generate_sn_data error logs.")
    else:
        summary["STAGE0"] = "SUCCESSFUL"
        write_summary()
#        if rank == 0:
#            with open(os.path.join(error_path, 'INPUT.INFO'), 'a') as f:
#                f.write(f"SACC Input Vector: {stage_1_command}\n")


    # Stage 2
    summary["STAGE1"] = "STARTED"
    write_summary()
    stage_2_command = f"cosmosis {ini} -p output.filename={output_path}/{ini.replace('.ini', '.txt')} --mpi"
    commands.append(f"\n Cosmosis Input Vector: {stage_2_command} \n")
    returncode = run_subprocess(stage_2_command, f"{error_path}/COSMOSIS_output_{ini}.log", f"{error_path}/COSMOSIS_output_ERROR_{ini}.err")
    if returncode != 0:
        summary["STAGE1"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
#        if rank == 0:
#            with open(os.path.join(error_path, 'INPUT.INFO'), 'a') as f:
#                f.write(f"Cosmosis Input Vector: {stage_2_command}\n")
        raise RuntimeError("Stage 2 failed. Check COSMOSIS error logs.")
    else:
        summary["STAGE1"] = "SUCCESSFUL"
        write_summary()
#        if rank == 0:
#            with open(os.path.join(error_path, 'INPUT.INFO'), 'a') as f:
#                f.write(f"Cosmosis Input Vector: {stage_2_command}\n")
    
    # Stage 3
    summary["STAGE2"] = "STARTED"
    write_summary()
    burnpath = os.path.join(output_path, str(ini.replace(".ini", ".txt")))
    stage_3_command = f"cosmosis-postprocess {output_path}/{ini.replace('.ini', '*.txt')} -o {plot_path} --burn {burnin(burnpath)}"
    commands.append(f"\n cosmosis-postprocess Input Vector: {stage_3_command}\n")
    returncode = run_subprocess(stage_3_command, f"{error_path}/PostProcess_output_{ini}.log", f"{error_path}/PostProcess_output_ERROR_{ini}.err")
    if returncode != 0:
        summary["STAGE2"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
#        if rank == 0:
#            with open(os.path.join(error_path, 'INPUT.INFO'), 'a') as f:
#                f.write(f"cosmosis-postprocess Input Vector: {stage_3_command}\n")
        raise RuntimeError("Stage 3 failed. Check PostProcess error logs.")
    else:
        summary["STAGE2"] = "SUCCESSFUL"
        write_summary()
#        if rank == 0:
#            with open(os.path.join(error_path, 'INPUT.INFO'), 'a') as f:
#                f.write(f"cosmosis-postprocess Input Vector: {stage_3_command}\n")
    # Stage 4
    summary["STAGE3"] = "STARTED"
    write_summary()
    try:
        # Initialize HD_read variable here
        f1 = os.path.join(path, hd)
        HD_read = pd.read_csv(f1, comment="#", sep=r"\s+")
        
        cosmo_params = pd.read_csv(
            os.path.join(plot_path, "means.txt"),
            sep=r"\s+",
            comment="#",
            header=None,
        ).T
        cosmo_params = cosmo_params.T.set_index(0).T
        summary["FoM"] = float(FoM(os.path.join(plot_path, "covmat.txt")))
        summary["Ndof"] = np.shape(HD_read)[0]
        summary["CPU_MINUTES"] = round((time.time() - time0) / 60, 2)  # in minutes
        summary["chi2"] = 22  # round(float(CHISQ.ch(COSMOSIS_PATH,ini)),3)  #22
        summary["sigint"] = 0.0
        summary["label"] = "none"
        summary["BLIND"] = 0
        summary["NWARNINGS"] = 1
        summary["w0"] = cosmo_params["cosmological_parameters--w"].iloc[0]
        summary["w0sig_marg"] = cosmo_params["cosmological_parameters--w"].iloc[1]
        summary["wa"] = cosmo_params["cosmological_parameters--wa"].iloc[0]
        summary["wasig_marg"] = cosmo_params["cosmological_parameters--wa"].iloc[1]
        summary["OM"] = cosmo_params["cosmological_parameters--omega_m"].iloc[0]
        summary["OMsig_marg"] = cosmo_params["cosmological_parameters--omega_m"].iloc[ 1]
        summary["STAGE3"] = "SUCCESSFUL"
        write_summary()
    except Exception as e:
        summary["STAGE3"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
        raise RuntimeError(f"Stage 4 failed with error: {str(e)}")
    return commands

def main():
    """Main function that orchestrates the different stages of the analysis."""
    # Parse command-line arguments
    args = parse_arguments()

    # Create the output directory if it doesn't exist
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    
    # Set up necessary directories
    setup_directories(args.outdir)

    # Check if files and paths exist
    check_files_and_paths([args.hd, args.cov], [args.path])
    if (os.path.split(args.ini)[0] == ''):
        ini_path = './'
    check_files_and_paths([os.path.split(args.ini)[1]], [ini_path])
    # Construct paths for error logs, output, and plots
    error_path = os.path.join(args.outdir , "ERROR_LOGS")
    output_path = os.path.join(args.outdir , "COSMOSIS-CHAINS")
    plot_path = os.path.join(args.outdir , "PLOTS")

    print("XXX",args.path, args.hd, args.cov, args.ini,error_path, output_path, plot_path)
    # Write to INPUT.INFO file
    with open(os.path.join(error_path, 'INPUT.INFO'), 'w') as f:
        f.write('STAGE 0 = ALL PATH AND FILES IN ARGUMENTS CHECK\n')
        f.write('STAGE 1 = generate_sn_data.py\n')
        f.write('STAGE 2 = COSMOSIS\n')
        f.write('STAGE 3 = POST PROCESSING (PLOT)\n\n')
        f.write('#Required Info\n')
        f.write(f'CWR: {os.getcwd()}\n')
        f.write(f'ARG_LIST: {sys.argv}\n')
        f.write(f'TIME_STAMP: {time.asctime()}\n')
        f.write(f'OUTPUT DIR: {args.outdir}\n')

    # Run the various stages of the analysis
    try:
        commands = run_stages(args.path, args.hd, args.cov, args.ini, error_path, output_path, plot_path)
        # Remove duplicates from the command list
        commands = list(set(commands))
        
        # Write the commands to the file
        with open(os.path.join(error_path, 'INPUT.INFO'), 'a') as f:
            for command in commands:
                f.write(f"{command}\n")
        
    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        print(traceback_str, file=sys.stderr)
        sys.exit(1)

    print("All stages completed successfully.")

if __name__ == "__main__":
    main()
