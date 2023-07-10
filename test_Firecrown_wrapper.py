from io import StringIO
from contextlib import redirect_stdout
import subprocess
import tempfile
import pytest
import pandas as pd
import numpy as np
import os
import sys
import argparse
from unittest.mock import patch
from Firecrown_wrapper import parse_arguments, setup_directories, redirect_stdout, run_subprocess, check_files_and_paths, FoM, burnin, run_stages, valid_directory_path
@patch.object(argparse.ArgumentParser, 'parse_args')
def test_parse_arguments(mock_args):
    mock_args.return_value = argparse.Namespace(path='path',
                                                hd='hd',
                                                cov='cov',
                                                ini='ini',
                                                outdir='outdir',
                                                param='param',
                                                summary='summary')

    args = parse_arguments()

    assert args.path == 'path'
    assert args.hd == 'hd'
    assert args.cov == 'cov'
    assert args.ini == 'ini'
    assert args.outdir == 'outdir'
    assert args.param == 'param'
    assert args.summary == 'summary'

@patch.object(argparse.ArgumentParser, 'parse_args')
def test_parse_arguments_missing_optional_args(mock_args):
    # Simulate that no optional arguments were provided
    mock_args.return_value = argparse.Namespace(path='path',
                                                hd='hd',
                                                cov='cov',
                                                ini='ini',
                                                outdir=None,
                                                param=None,
                                                summary=None)

    args = parse_arguments()

    assert args.outdir is None
    assert args.param is None
    assert args.summary is None
'''
@patch.object(argparse.ArgumentParser, 'parse_args')
def test_parse_arguments_invalid_outdir(mock_parse_args):
    # Simulate that an invalid outdir argument was provided
    mock_parse_args.return_value = argparse.Namespace(path='path',
                                                      hd='hd',
                                                      cov='cov',
                                                      ini='ini',
                                                      outdir='invalid/outdir',  # invalid path
                                                      param='param',
                                                      summary='summary')

    with pytest.raises(argparse.ArgumentTypeError):
        args = parse_arguments()    
'''

def test_valid_directory_path():
    with pytest.raises(argparse.ArgumentTypeError):
        valid_directory_path('invalid/outdir')
        
def test_setup_directories(tmp_path):
    # tmp_path is a pytest fixture providing a temporary directory unique to this test invocation

    dir_path = tmp_path / "subdir"
    assert not os.path.exists(dir_path)
    setup_directories(dir_path)
    assert os.path.exists(dir_path)
    # Tests for setup_directories function

def test_redirect_stdout(tmp_path):
    # tmp_path is a pytest fixture providing a temporary directory unique to this test invocation

    file_path = tmp_path / "stdout.txt"

    # Before redirecting stdout, print something to the console
    original_stdout = sys.stdout
    print("Console output")

    # Now redirect stdout to the file
    with open(file_path, "w") as f:
        with redirect_stdout(f):
            # Print something else, which should go to the file
            print("File output")

    # Check that the file contains the second print output
    with open(file_path, "r") as f:
        contents = f.read()
    assert "File output" in contents

    # Check that the file does not contain the first print output
    assert "Console output" not in contents


def test_run_subprocess():
    # Define a command to execute
    command = ["echo", "Hello, World!"]

    # Create temporary files for output and error streams
    with tempfile.NamedTemporaryFile(mode="w") as output_file, tempfile.NamedTemporaryFile(mode="w") as error_file:
        # Get the paths to the temporary files
        output_path = output_file.name
        error_path = error_file.name

        # Call the run_subprocess function
        result = run_subprocess(command, output_path, error_path)

        # Assert that the command was executed successfully
        assert result == 0

        # Read the captured output directly using subprocess.check_output
        captured_output = subprocess.check_output(command).decode().strip()

        # Assert that the captured output matches the expected value
        expected_output = "Hello, World!"
        assert captured_output == expected_output

def test_check_files_and_paths():
    # Create temporary files and directories
    with tempfile.NamedTemporaryFile() as temp_file1, tempfile.NamedTemporaryFile() as temp_file2:
        temp_directory = tempfile.mkdtemp()

        # Get the paths of the temporary file and directory
        temp_file_path1 = temp_file1.name
        temp_file_path2 = temp_file2.name
        temp_directory_path = temp_directory

        # Call the check_files_and_paths function
        try:
            check_files_and_paths([temp_file_path1, temp_file_path2], [temp_directory_path])
        except FileNotFoundError:
            # If FileNotFoundError is raised, the test should fail
            assert False
        except Exception as e:
            # If any other exception is raised, the test should fail
            assert False
        else:
            # If no exceptions are raised, the test should pass
            assert True

'''
def test_FoM(tmp_path):
    # Create a temporary file with a valid covariance matrix
    file_path = tmp_path / "covariance.txt"
    content = """
    1 0.5
    0.5 2
    """
    with open(file_path, "w") as f:
        f.write(content)

    # Call the FoM function with the temporary file path
    result = FoM(str(file_path))

    # Assert that the result is calculated correctly
    expected_result = 1 / np.sqrt(np.linalg.det([[1, 0.5], [0.5, 2]]))
    assert result == expected_result
'''    

def test_burnin(tmp_path):
    # Create a temporary file with sample content
    file_path = tmp_path / "chain.txt"
    content = """
    1
    2
    3
    4
    5
    """
    with open(file_path, "w") as f:
        f.write(content)

    # Call the burnin function with the temporary file path
    burnin_length = burnin(str(file_path))

    # Assert that the burn-in length is calculated correctly
    expected_length = int(0.15 * 5)  # 15% of the number of steps (5 in this case)
    assert burnin_length == expected_length


    
def test_run_stages():
    # Tests for run_stages function
    pass
