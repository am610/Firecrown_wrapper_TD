"""
Unit and integration tests for Firecrown_wrapper module.

Tests cover:
- Argument parsing and validation
- Directory setup
- File and path validation
- Subprocess execution via SubprocessExecutor
- Math functions (FoM, burnin)
- Error handling and edge cases
"""

import argparse
from pathlib import Path
import sys

import pytest
import pandas as pd
import numpy as np
import yaml
from unittest.mock import patch
import Firecrown_wrapper as wrapper
from Firecrown_wrapper import (
    parse_arguments,
    setup_directories,
    redirect_stdout,
    check_files_and_paths,
    FoM,
    burnin,
    valid_directory_path,
    write_summary,
)
from subprocess_executor import get_executor


class TestArgumentParsing:
    """Test command-line argument parsing and validation."""

    def test_valid_directory_path_valid(self, tmp_path):
        """Test valid_directory_path with a real directory."""
        result = valid_directory_path(str(tmp_path))
        assert result == str(tmp_path)

    def test_valid_directory_path_invalid(self):
        """Test valid_directory_path with an invalid directory."""
        with pytest.raises(argparse.ArgumentTypeError):
            valid_directory_path('/nonexistent/invalid/path/12345')

    @patch('sys.argv', ['prog', '/tmp', 'hd.txt', 'cov.txt', 'cosmosis.ini'])
    def test_parse_arguments_mandatory(self, tmp_path):
        """Test parsing mandatory arguments."""
        with patch('argparse.ArgumentParser.parse_args') as mock_args:
            mock_args.return_value = argparse.Namespace(
                path=str(tmp_path),
                hd='hd.txt',
                cov='cov.txt',
                ini='cosmosis.ini',
                outdir=str(tmp_path),
                param='',
                summary='SUMMARY.YAML'
            )
            args = parse_arguments()
            assert args.hd == 'hd.txt'
            assert args.cov == 'cov.txt'
            assert args.ini == 'cosmosis.ini'

    @patch('sys.argv', ['prog', '/tmp', 'hd.txt', 'cov.txt', 'cosmosis.ini'])
    def test_parse_arguments_with_optional(self, tmp_path):
        """Test parsing with optional arguments."""
        with patch('argparse.ArgumentParser.parse_args') as mock_args:
            mock_args.return_value = argparse.Namespace(
                path=str(tmp_path),
                hd='hd.txt',
                cov='cov.txt',
                ini='cosmosis.ini',
                outdir=str(tmp_path),
                param='param.value=42',
                summary='custom_summary.yaml'
            )
            args = parse_arguments()
            assert args.param == 'param.value=42'
            assert args.summary == 'custom_summary.yaml'

    def test_write_summary_respects_configured_summary_path(self, tmp_path):
        """Test that write_summary writes to the configured summary path."""
        summary_path = tmp_path / "custom_summary.yaml"
        previous_summary_path = wrapper.SUMMARY_PATH
        previous_stage0 = wrapper.summary["STAGE0"]

        try:
            wrapper.SUMMARY_PATH = Path(summary_path)
            wrapper.summary["STAGE0"] = "TESTING"
            write_summary()

            with open(summary_path, "r", encoding="utf-8") as handle:
                loaded = yaml.safe_load(handle)
            assert loaded["STAGE0"] == "TESTING"
        finally:
            wrapper.SUMMARY_PATH = previous_summary_path
            wrapper.summary["STAGE0"] = previous_stage0


class TestDirectorySetup:
    """Test directory creation and setup."""

    def test_setup_directories_creates_subdirs(self, tmp_path):
        """Test that setup_directories creates all required subdirectories."""
        output_path = tmp_path / "output"
        output_path.mkdir()
        
        setup_directories(str(output_path))
        
        expected_dirs = ["ERROR_LOGS", "COSMOSIS-CHAINS", "PLOTS"]
        for subdir in expected_dirs:
            assert (output_path / subdir).exists(), f"{subdir} was not created"

    def test_setup_directories_idempotent(self, tmp_path):
        """Test that setup_directories can be called multiple times safely."""
        output_path = tmp_path / "output"
        output_path.mkdir()
        
        setup_directories(str(output_path))
        setup_directories(str(output_path))  # Call twice
        
        expected_dirs = ["ERROR_LOGS", "COSMOSIS-CHAINS", "PLOTS"]
        for subdir in expected_dirs:
            assert (output_path / subdir).exists()


class TestStdoutRedirection:
    """Test stdout redirection context manager."""

    def test_redirect_stdout_to_file(self, tmp_path):
        """Test that output is redirected to file."""
        file_path = tmp_path / "output.txt"
        
        with open(file_path, "w") as f:
            with redirect_stdout(f):
                print("Test output")
        
        with open(file_path, "r") as f:
            contents = f.read()
        
        assert "Test output" in contents

    def test_redirect_stdout_restores(self, tmp_path):
        """Test that stdout is restored after redirection."""
        original_stdout = sys.stdout
        file_path = tmp_path / "output.txt"
        
        with open(file_path, "w") as f:
            with redirect_stdout(f):
                pass
        
        assert sys.stdout == original_stdout


class TestSubprocessExecutor:
    """Test SubprocessExecutor class."""

    def test_executor_initialization(self):
        """Test SubprocessExecutor initialization."""
        executor = get_executor(timeout=3600)
        assert executor.default_timeout == 3600

    def test_executor_custom_timeout(self):
        """Test SubprocessExecutor with custom timeout."""
        executor = get_executor(timeout=1800)
        assert executor.default_timeout == 1800

    def test_executor_run_success(self, tmp_path):
        """Test successful subprocess execution via executor."""
        executor = get_executor()
        output_file = tmp_path / "output.txt"
        error_file = tmp_path / "error.txt"
        
        returncode = executor.run(
            "echo 'success'",
            str(output_file),
            str(error_file),
            description="Test successful execution"
        )
        
        assert returncode == 0
        assert output_file.exists()
        assert error_file.exists()

    def test_executor_run_failure(self, tmp_path):
        """Test subprocess failure handling via executor."""
        executor = get_executor()
        output_file = tmp_path / "output.txt"
        error_file = tmp_path / "error.txt"
        
        returncode = executor.run(
            f"{sys.executable} -c \"import sys; sys.exit(1)\"",
            str(output_file),
            str(error_file),
            description="Test failure handling"
        )
        
        assert returncode != 0

    def test_executor_run_timeout(self, tmp_path):
        """Test subprocess timeout handling via executor."""
        executor = get_executor()
        output_file = tmp_path / "output.txt"
        error_file = tmp_path / "error.txt"
        
        with pytest.raises(RuntimeError, match="timed out"):
            executor.run(
                f"{sys.executable} -c \"import time; time.sleep(100)\"",
                str(output_file),
                str(error_file),
                timeout=1,
                description="Test timeout handling"
            )

    def test_executor_run_pipeline_success(self, tmp_path):
        """Test successful pipeline execution via executor."""
        executor = get_executor()
        
        commands = [
            {'command': 'echo "stage1"', 'description': 'Stage 1'},
            {'command': 'echo "stage2"', 'description': 'Stage 2'}
        ]
        
        success_results, failure_results = executor.run_pipeline(
            commands,
            str(tmp_path),
            str(tmp_path),
            timeout=10
        )
        
        assert len(success_results) == 2
        assert len(failure_results) == 0
        assert success_results[0]['index'] == 0
        assert success_results[1]['index'] == 1

    def test_executor_run_pipeline_with_failure(self, tmp_path):
        """Test pipeline with failure stopping execution."""
        executor = get_executor()
        
        commands = [
            {'command': 'echo "stage1"', 'description': 'Stage 1'},
            {'command': f'{sys.executable} -c "import sys; sys.exit(1)"', 'description': 'Stage 2 - fails'},
            {'command': 'echo "stage3"', 'description': 'Stage 3'}
        ]
        
        success_results, failure_results = executor.run_pipeline(
            commands,
            str(tmp_path),
            str(tmp_path),
            timeout=10,
            stop_on_failure=True
        )
        
        assert len(success_results) == 1
        assert len(failure_results) == 1
        # Pipeline should stop after first failure
        assert failure_results[0]['index'] == 1


class TestFilePathValidation:
    """Test file and path checking."""

    def test_check_files_and_paths_valid(self, tmp_path):
        """Test validation with valid files and paths."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        # Should not raise
        check_files_and_paths(
            ["file1.txt", "file2.txt"],
            [str(tmp_path)]
        )

    def test_check_files_and_paths_missing_directory(self):
        """Test validation with missing directory."""
        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            check_files_and_paths(
                ["file.txt"],
                ["/nonexistent/directory/12345"]
            )

    def test_check_files_and_paths_missing_file(self, tmp_path):
        """Test validation with missing file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            check_files_and_paths(
                ["nonexistent.txt"],
                [str(tmp_path)]
            )

    def test_check_files_and_paths_multiple_files(self, tmp_path):
        """Test validation with multiple files."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")
        
        check_files_and_paths(
            ["file1.txt", "file2.txt"],
            [str(tmp_path)]
        )


class TestFoM:
    """Test Figure of Merit calculation."""

    def test_FoM_valid_matrix(self, tmp_path):
        """Test FoM calculation with valid covariance matrix."""
        file_path = tmp_path / "covmat.txt"
        
        # Create a valid covariance matrix with required columns
        df = pd.DataFrame({
            'cosmological_parameters--w': [1.0, 0.5, 0.5, 2.0],
            'cosmological_parameters--wa': [0.5, 2.0, 1.5, 0.3],
            'other_param': [1.0, 2.0, 3.0, 4.0]
        })
        df.to_csv(file_path, sep='\t', index=False)
        
        result = FoM(str(file_path))
        
        assert isinstance(result, (float, np.floating))
        assert result > 0

    def test_FoM_missing_file(self, tmp_path):
        """Test FoM with non-existent file."""
        with pytest.raises(FileNotFoundError):
            FoM(str(tmp_path / "nonexistent.txt"))

    def test_FoM_missing_parameters(self, tmp_path):
        """Test FoM with missing required parameters."""
        file_path = tmp_path / "covmat.txt"
        
        df = pd.DataFrame({
            'other_param1': [1.0, 2.0],
            'other_param2': [3.0, 4.0]
        })
        df.to_csv(file_path, sep='\t', index=False)
        
        with pytest.raises(ValueError, match="Expected to find 2 cosmological parameters"):
            FoM(str(file_path))


class TestBurnin:
    """Test burn-in calculation."""

    def test_burnin_valid_chain(self, tmp_path):
        """Test burn-in calculation with valid chain file."""
        file_path = tmp_path / "chain.txt"
        
        # Create a chain file with 100 lines
        lines = [f"{i}" for i in range(100)]
        file_path.write_text('\n'.join(lines))
        
        result = burnin(str(file_path))
        
        # 15% of 100 = 15
        assert result == 15

    def test_burnin_small_chain(self, tmp_path):
        """Test burn-in with small chain file."""
        file_path = tmp_path / "chain.txt"
        
        lines = [f"{i}" for i in range(10)]
        file_path.write_text('\n'.join(lines))
        
        result = burnin(str(file_path))
        
        # 15% of 10 = 1.5 -> int(1.5) = 1
        assert result == 1

    def test_burnin_missing_file(self, tmp_path):
        """Test burn-in with non-existent file."""
        with pytest.raises(FileNotFoundError):
            burnin(str(tmp_path / "nonexistent.txt"))

    def test_burnin_empty_file(self, tmp_path):
        """Test burn-in with empty file."""
        file_path = tmp_path / "chain.txt"
        file_path.write_text('')
        
        result = burnin(str(file_path))
        assert result == 0


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_integration_setup_and_validation(self, tmp_path):
        """Test complete setup and validation workflow."""
        # Create input files
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        hd_file = input_dir / "hd.txt"
        cov_file = input_dir / "cov.txt"
        ini_file = tmp_path / "cosmosis.ini"
        
        hd_file.write_text("# HD data\n1 2 3\n")
        cov_file.write_text("# Covariance\n1 0\n0 1\n")
        ini_file.write_text("[test]\nvalue=1\n")
        
        # Setup output directories
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        setup_directories(str(output_dir))
        
        # Validate all directories were created
        expected_dirs = ["ERROR_LOGS", "COSMOSIS-CHAINS", "PLOTS"]
        for subdir in expected_dirs:
            assert (output_dir / subdir).exists()
        
        # Validate files exist
        check_files_and_paths(
            ["hd.txt", "cov.txt"],
            [str(input_dir)]
        )

    def test_integration_file_validation_workflow(self, tmp_path):
        """Test file validation in realistic workflow."""
        # Setup directories
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        
        # Create required files
        (data_dir / "hubble.txt").write_text("# Data")
        (data_dir / "covariance.txt").write_text("# Cov")
        
        # Validate files exist
        check_files_and_paths(
            ["hubble.txt", "covariance.txt"],
            [str(data_dir)]
        )

    def test_integration_executor_usage(self, tmp_path):
        """Test SubprocessExecutor integration in workflow."""
        executor = get_executor()
        
        # Simulate a pipeline with multiple stages
        commands = [
            {'command': 'echo "Generating data"', 'description': 'Stage 0: Generate SACC'},
            {'command': 'echo "Running analysis"', 'description': 'Stage 1: COSMOSIS'},
        ]
        
        success_results, failure_results = executor.run_pipeline(
            commands,
            str(tmp_path),
            str(tmp_path),
            timeout=10
        )
        
        assert len(success_results) == 2
        assert len(failure_results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
