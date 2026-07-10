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
    check_files_and_paths() - Checks if specified files and directories exist.
    run_stages() - Runs the various stages of the analysis.
    burnin() - Calculates the burn-in length for a MCMC chain.
    main() - The main function that calls all the above functions in sequence.

The subprocess execution is handled by the SubprocessExecutor module for
consistent error handling, logging, and timeout management.
"""

import argparse
import os
import pathlib
import sys
import time
import traceback
import numpy as np
import pandas as pd
import yaml
import logging
import itertools
from contextlib import contextmanager
from subprocess_executor import get_executor

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
    """Write the current summary state to SUMMARY.YAML file."""
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
    """Validate that a string is a valid directory path."""
    if not os.path.isdir(string):
        raise argparse.ArgumentTypeError(f"{string} is not a valid directory path")
    return string
        
def parse_arguments():
    """Parse and validate command-line arguments."""
    usage = "Mandatory arguments required in fixed order"
    parser = argparse.ArgumentParser(description=usage)
    parser.add_argument("path", help="Path for the HD and COV", type=valid_directory_path)
    parser.add_argument("hd", help="HD file name")
    parser.add_argument("cov", help="COV file name")
    parser.add_argument("ini", help="*.ini file for COSMOSIS")
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
    """
    Create necessary output directories for the analysis.
    
    Creates subdirectories: ERROR_LOGS, COSMOSIS-CHAINS, PLOTS
    
    Args:
        output_path (str): The base output directory path
    """
    subdirs = ["ERROR_LOGS", "COSMOSIS-CHAINS", "PLOTS"]
    for subdir in subdirs:
        dir_path = os.path.join(output_path, subdir)
        try:
            os.makedirs(dir_path, exist_ok=True)
        except FileExistsError:
            pass  # Directory already exists


def check_files_and_paths(files, dir_paths):
    """
    Check if the specified files and directories exist.
    
    Args:
        files (list): List of file names to check
        dir_paths (list): List of directory paths to check files in
        
    Raises:
        FileNotFoundError: If any file or directory is missing
    """
    for dir_path in dir_paths:
        if not os.path.isdir(dir_path):
            raise FileNotFoundError(f"Directory does not exist: {dir_path}")
        for file in files:
            file_full_path = os.path.join(dir_path, file)
            if not os.path.isfile(file_full_path):
                raise FileNotFoundError(f"File not found: {file_full_path}")


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
        
    Raises
    ------
    FileNotFoundError: If input file does not exist
    ValueError: If covariance matrix cannot be extracted
    """
    try:
        a = pd.read_csv(input_file, sep=r"\s+")
    except FileNotFoundError:
        logging.error(f"Covariance file not found: {input_file}")
        raise
    except Exception as e:
        logging.error(f"Error reading covariance file: {str(e)}")
        raise
        
    mat = np.asarray(a)
    names = ["cosmological_parameters--w", "cosmological_parameters--wa"]
    ind = []
    FoM_COV = []
    
    for n in list(a):
        if n == names[0] or n == names[1]:
            N = list(a).index(n)
            ind.append(N)
    
    if len(ind) != 2:
        raise ValueError(f"Expected to find 2 cosmological parameters, found {len(ind)}")
    
    cov = list(itertools.product(ind, repeat=2))
    for i in cov:
        tmp = mat[i]
        FoM_COV.append(tmp)
    FoM_COV = np.reshape(FoM_COV, (2, 2))
    X = np.linalg.det(FoM_COV)
    
    if X <= 0:
        logging.warning(f"Covariance matrix determinant is non-positive: {X}")
    
    FoM = 1 / np.sqrt(abs(X))
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
        
    Raises
    ------
    FileNotFoundError: If chain file does not exist
    """
    try:
        a = pd.read_csv(chain, comment="#", header=None, sep=r"\s+")
        L = int(0.15 * a.shape[0])
        return L
    except FileNotFoundError:
        logging.error(f"Chain file not found: {chain}")
        raise
    except pd.errors.EmptyDataError:
        logging.warning(f"Chain file is empty: {chain}")
        return 0
    except Exception as e:
        logging.error(f"Error reading chain file: {str(e)}")
        raise


def run_stages(path, hd, cov, ini, error_path, output_path, plot_path):
    """
    Run the various stages of the analysis using SubprocessExecutor.
    
    Stage 0: Generate SACC file from SN data
    Stage 1: Run COSMOSIS for parameter estimation
    Stage 2: Post-process results and generate plots
    Stage 3: Extract and summarize cosmological parameters
    
    Args:
        path (str): Path to HD and COV files
        hd (str): HD file name
        cov (str): COV file name
        ini (str): COSMOSIS ini file name
        error_path (str): Path for error/log files
        output_path (str): Path for COSMOSIS output chains
        plot_path (str): Path for plots and analysis results
        
    Returns:
        list: List of executed commands
        
    Raises:
        RuntimeError: If any stage fails
    """
    # Initialize subprocess executor with 1-hour timeout
    executor = get_executor(timeout=3600)
    commands = []
    
    # Stage 0: Generate SACC data
    summary["STAGE0"] = "STARTED"
    write_summary()

    PWD = os.getcwd()
    sacc_file = os.path.join(PWD, "srd-y1-converted.sacc")
    
    # Remove any preexisting sacc file
    try:
        if os.path.exists(sacc_file):
            os.remove(sacc_file)
    except Exception as e:
        logging.warning(f"Could not remove existing SACC file: {e}")

    stage_0_command = f"python $FIRECROWN_EXAMPLES_DIR/srd_sn/generate_sn_data.py {path} {hd} {cov}"
    commands.append(f"\nSACC Input Vector: {stage_0_command}\n")
    
    try:
        returncode = executor.run(
            stage_0_command, 
            f"{error_path}/generate_sn_data_output_{ini}.log", 
            f"{error_path}/generate_sn_data_output_ERROR_{ini}.err",
            description="Stage 0: Generate SACC file from SN data"
        )
        
        if returncode != 0:
            summary["STAGE0"] = "FAILED"
            summary["ABORT_IF_ZERO"] = 0
            write_summary()
            raise RuntimeError("Stage 0 (SACC generation) failed. Check generate_sn_data error logs.")
        else:
            summary["STAGE0"] = "SUCCESSFUL"
            write_summary()
            logging.info("Stage 0 (SACC generation) completed successfully.")
    except RuntimeError as e:
        summary["STAGE0"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
        raise

    # Stage 1: Run COSMOSIS
    summary["STAGE1"] = "STARTED"
    write_summary()
    
    stage_1_command = (
        f"cosmosis {ini} "
        f"-p firecrown_likelihood.sacc_file={os.getcwd()}/srd-y1-converted.sacc "
        f"output.filename={output_path}/{ini.replace('.ini', '.txt')} "
        f"--mpi"
    )
    commands.append(f"\nCosmosis Input Vector: {stage_1_command}\n")
    
    try:
        returncode = executor.run(
            stage_1_command, 
            f"{error_path}/COSMOSIS_output_{ini}.log", 
            f"{error_path}/COSMOSIS_output_ERROR_{ini}.err",
            description="Stage 1: Run COSMOSIS for parameter estimation"
        )
        
        if returncode != 0:
            summary["STAGE1"] = "FAILED"
            summary["ABORT_IF_ZERO"] = 0
            write_summary()
            raise RuntimeError("Stage 1 (COSMOSIS) failed. Check COSMOSIS error logs.")
        else:
            summary["STAGE1"] = "SUCCESSFUL"
            write_summary()
            logging.info("Stage 1 (COSMOSIS) completed successfully.")
    except RuntimeError as e:
        summary["STAGE1"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
        raise
    
    # Stage 2: Post-processing
    summary["STAGE2"] = "STARTED"
    write_summary()
    
    burnpath = os.path.join(output_path, str(ini.replace(".ini", ".txt")))
    burn_length = burnin(burnpath)
    
    stage_2_command = (
        f"cosmosis-postprocess {output_path}/{ini.replace('.ini', '*.txt')} "
        f"-o {plot_path} "
        f"--burn {burn_length}"
    )
    commands.append(f"\nCosmosis-postprocess Input Vector: {stage_2_command}\n")
    
    try:
        returncode = executor.run(
            stage_2_command, 
            f"{error_path}/PostProcess_output_{ini}.log", 
            f"{error_path}/PostProcess_output_ERROR_{ini}.err",
            description="Stage 2: Post-process results and generate plots"
        )
        
        if returncode != 0:
            summary["STAGE2"] = "FAILED"
            summary["ABORT_IF_ZERO"] = 0
            write_summary()
            raise RuntimeError("Stage 2 (Post-processing) failed. Check PostProcess error logs.")
        else:
            summary["STAGE2"] = "SUCCESSFUL"
            write_summary()
            logging.info("Stage 2 (Post-processing) completed successfully.")
    except RuntimeError as e:
        summary["STAGE2"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
        raise
    
    # Stage 3: Extract cosmological parameters
    summary["STAGE3"] = "STARTED"
    write_summary()
    
    try:
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
        summary["CPU_MINUTES"] = round((time.time() - time0) / 60, 2)
        
        # TODO: Fix chi2 calculation. Currently hardcoded to 22 pending CHISQ module integration.
        summary["chi2"] = None  # Placeholder - requires CHISQ module implementation
        summary["sigint"] = 0.0
        summary["label"] = "none"
        summary["BLIND"] = 0
        summary["NWARNINGS"] = 1
        summary["w0"] = cosmo_params["cosmological_parameters--w"].iloc[0]
        summary["w0sig_marg"] = cosmo_params["cosmological_parameters--w"].iloc[1]
        summary["wa"] = cosmo_params["cosmological_parameters--wa"].iloc[0]
        summary["wasig_marg"] = cosmo_params["cosmological_parameters--wa"].iloc[1]
        summary["OM"] = cosmo_params["cosmological_parameters--omega_m"].iloc[0]
        summary["OMsig_marg"] = cosmo_params["cosmological_parameters--omega_m"].iloc[1]
        summary["STAGE3"] = "SUCCESSFUL"
        write_summary()
        logging.info("Stage 3 (Parameter extraction) completed successfully.")
        
    except Exception as e:
        summary["STAGE3"] = "FAILED"
        summary["ABORT_IF_ZERO"] = 0
        write_summary()
        logging.error(f"Stage 3 failed with error: {str(e)}")
        raise RuntimeError(f"Stage 3 (Parameter extraction) failed: {str(e)}") from e
    
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
    
    if os.path.split(args.ini)[0] == '':
        ini_path = './'
    else:
        ini_path = os.path.split(args.ini)[0]
    
    check_files_and_paths([os.path.split(args.ini)[1]], [ini_path])
    
    # Construct paths for error logs, output, and plots
    error_path = os.path.join(args.outdir, "ERROR_LOGS")
    output_path = os.path.join(args.outdir, "COSMOSIS-CHAINS")
    plot_path = os.path.join(args.outdir, "PLOTS")

    # Write to INPUT.INFO file
    with open(os.path.join(error_path, 'INPUT.INFO'), 'w') as f:
        f.write('STAGE 0 = Generate SACC file from SN data\n')
        f.write('STAGE 1 = COSMOSIS parameter estimation\n')
        f.write('STAGE 2 = POST PROCESSING (PLOT)\n')
        f.write('STAGE 3 = Extract cosmological parameters\n\n')
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
        
        print("All stages completed successfully.")
        logging.info("Pipeline execution completed successfully.")
        
    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"An error occurred: {e}", file=sys.stderr)
        traceback.print_exc()
        print(traceback_str, file=sys.stderr)
        logging.error(f"Pipeline failed: {traceback_str}")
        sys.exit(1)

if __name__ == "__main__":
    main()
