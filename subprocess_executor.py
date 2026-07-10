"""
Subprocess orchestration and execution utilities for Firecrown wrapper.

This module provides a clean abstraction for managing subprocess execution,
logging, and error handling. It decouples subprocess management from the
main pipeline logic.
"""

import subprocess
import logging
from typing import Optional, Tuple

# Configure logger
logger = logging.getLogger(__name__)


class SubprocessExecutor:
    """
    Manages subprocess execution with consistent error handling and logging.
    
    Attributes:
        default_timeout (int): Default timeout in seconds for all subprocess calls
    """
    
    def __init__(self, default_timeout: int = 3600):
        """
        Initialize the subprocess executor.
        
        Args:
            default_timeout (int): Default timeout in seconds (default: 1 hour)
        """
        self.default_timeout = default_timeout
    
    def run(
        self,
        command: str,
        output_file: str,
        error_file: str,
        timeout: Optional[int] = None,
        description: str = ""
    ) -> int:
        """
        Execute a command in a subprocess with captured output.
        
        Args:
            command (str): The shell command to execute
            output_file (str): Path to file for stdout
            error_file (str): Path to file for stderr
            timeout (int, optional): Override default timeout in seconds
            description (str, optional): Human-readable description of the command
            
        Returns:
            int: The return code from the subprocess
            
        Raises:
            subprocess.TimeoutExpired: If command exceeds timeout
            RuntimeError: If subprocess execution fails
        """
        timeout = timeout or self.default_timeout
        cmd_desc = description or command[:80]
        
        try:
            logger.info(f"Starting subprocess: {cmd_desc}")
            logger.debug(f"Full command: {command}")
            
            with open(output_file, "w") as out_f, open(error_file, "w") as err_f:
                process = subprocess.run(
                    command,
                    shell=True,
                    stdout=out_f,
                    stderr=err_f,
                    timeout=timeout,
                    text=True
                )
            
            if process.returncode == 0:
                logger.info(f"Subprocess completed successfully: {cmd_desc}")
            else:
                logger.warning(
                    f"Subprocess exited with code {process.returncode}: {cmd_desc}\n"
                    f"  stdout: {output_file}\n"
                    f"  stderr: {error_file}"
                )
            
            return process.returncode
            
        except subprocess.TimeoutExpired as e:
            logger.error(
                f"Subprocess timed out after {timeout} seconds: {cmd_desc}\n"
                f"  Command: {command}"
            )
            raise RuntimeError(
                f"Subprocess timed out after {timeout}s: {cmd_desc}"
            ) from e
            
        except Exception as e:
            logger.error(
                f"Subprocess execution failed: {cmd_desc}\n"
                f"  Error: {str(e)}"
            )
            raise RuntimeError(
                f"Subprocess execution failed: {str(e)}"
            ) from e
    
    def run_pipeline(
        self,
        commands: list,
        output_base_path: str,
        error_base_path: str,
        timeout: Optional[int] = None,
        stop_on_failure: bool = True
    ) -> Tuple[list, list]:
        """
        Execute a sequence of commands in order.
        
        Args:
            commands (list): List of command dicts with 'command', 'description' keys
                Example: [
                    {'command': 'cmd1', 'description': 'Stage 1'},
                    {'command': 'cmd2', 'description': 'Stage 2'}
                ]
            output_base_path (str): Base directory for output files
            error_base_path (str): Base directory for error files
            timeout (int, optional): Override default timeout for all commands
            stop_on_failure (bool): If True, stop pipeline on first failure
            
        Returns:
            Tuple[list, list]: (success_results, failure_results)
                Each result is a dict with 'index', 'description', 'returncode'
        """
        success_results = []
        failure_results = []
        
        for idx, cmd_dict in enumerate(commands):
            command = cmd_dict.get('command')
            description = cmd_dict.get('description', f"Command {idx}")
            
            if not command:
                logger.warning(f"Skipping command {idx}: no 'command' key")
                continue
            
            output_file = f"{output_base_path}/stage_{idx}.log"
            error_file = f"{error_base_path}/stage_{idx}.err"
            
            try:
                returncode = self.run(
                    command,
                    output_file,
                    error_file,
                    timeout=timeout,
                    description=description
                )
                
                if returncode == 0:
                    success_results.append({
                        'index': idx,
                        'description': description,
                        'returncode': returncode
                    })
                else:
                    failure_results.append({
                        'index': idx,
                        'description': description,
                        'returncode': returncode
                    })
                    
                    if stop_on_failure:
                        logger.error(
                            f"Pipeline stopped at stage {idx} ({description}) "
                            f"due to failure"
                        )
                        break
                        
            except Exception as e:
                logger.error(f"Exception in pipeline stage {idx}: {str(e)}")
                failure_results.append({
                    'index': idx,
                    'description': description,
                    'error': str(e)
                })
                
                if stop_on_failure:
                    break
        
        return success_results, failure_results


def get_executor(timeout: int = 3600) -> SubprocessExecutor:
    """
    Factory function to create a subprocess executor instance.
    
    Args:
        timeout (int): Default timeout in seconds
        
    Returns:
        SubprocessExecutor: Configured executor instance
    """
    return SubprocessExecutor(default_timeout=timeout)
