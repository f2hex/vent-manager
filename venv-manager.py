#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "rich",
# ]
# ///

# Program to manage all the python virtual envs that can be found in a specific directory tree
# The only requirement to run this program is to have uv installed.
# Author: Franco Fiorese <fcoder@f2hex.net> Jan 2025
#
#


import os
from pathlib import Path
import shutil
import argparse
import sys
from datetime import datetime
import subprocess
import json
import traceback
from dataclasses import dataclass
from typing import List, Optional, Dict
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console

@dataclass
class VirtualEnv:
    """Data class to store virtual environment information."""
    path: Path
    size_mb: float
    age_days: int
    is_broken: bool = False
    packages: List[Dict[str, str]] = None

    @property
    def size_formatted(self) -> str:
        """Format size in MB with thousands separator and 2 decimal places."""
        return f"{self.size_mb:,.2f}"

class VenvScanner:
    """Class to handle virtual environment scanning and management."""
    def __init__(self, console: Console, verbose: bool = False):
        self.console = console
        self.verbose = verbose

    def _get_python_path(self, venv_path: Path) -> Path:
        """Determine the Python executable path based on OS."""
        if sys.platform == "win32":
            python_path = venv_path / "Scripts" / "python.exe"
        else:
            python_path = venv_path / "bin" / "python"

        return python_path.resolve() if python_path.is_symlink() else python_path

    def get_venv_packages(self, venv_path: Path) -> Optional[List[Dict[str, str]]]:
        """Get list of installed packages in a virtual environment."""
        python_path = self._get_python_path(venv_path)

        if not python_path.exists():
            if self.verbose:
                self.console.print(f"[bold yellow]Warning[/]: {venv_path} does not have a valid python executable")
            return None

        try:
            cmd = [str(python_path), "-m", "pip", "list", "--format", "json"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            packages = json.loads(result.stdout)
            return [{'name': pkg['name'], 'version': pkg['version']} for pkg in packages]
        except (subprocess.CalledProcessError, json.JSONDecodeError, Exception) as e:
            if self.verbose:
                self.console.print(f"[bold red]Error[/]: Failed to get package list for {venv_path}: {str(e)}")
            return None

    def is_virtualenv(self, path: Path) -> bool:
        """Check if a directory is a Python virtual environment."""
        venv_markers = ['pyvenv.cfg', 'bin/python', 'Scripts/python.exe', 'Lib/site-packages']
        return any((path / marker).exists() for marker in venv_markers)

    @staticmethod
    def get_dir_size(path: Path) -> float:
        """Calculate total directory size in MB."""
        total_bytes = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return total_bytes / (1024 * 1024)

    @staticmethod
    def get_dir_age_days(path: Path) -> int:
        """Get directory age in days based on most recent file modification."""
        try:
            most_recent = max(f.stat().st_mtime for f in path.rglob('*') if f.is_file())
            age = datetime.now() - datetime.fromtimestamp(most_recent)
            return age.days
        except ValueError:
            return 0

    @staticmethod
    def trim_path(path_str: str, max_length: int = 132) -> str:
        """Trim path to max_length characters, preserving the end of the path."""
        if len(path_str) <= max_length:
            return path_str

        path_parts = path_str.split(os.sep)
        end_parts = path_parts[-2:]
        end_len = len(os.sep.join(end_parts))
        available_start = max_length - end_len - 5

        if available_start <= 0:
            return f"...{os.sep}{end_parts[-1]}"

        start = path_parts[0]
        for part in path_parts[1:-2]:
            if len(f"{start}{os.sep}{part}") <= available_start:
                start = f"{start}{os.sep}{part}"
            else:
                break

        return f"{start}{os.sep}...{os.sep}{os.sep.join(end_parts)}"

    def scan_virtualenvs(self, root_path: Path, older_than_days: Optional[int] = None) -> List[VirtualEnv]:
        """Scan for virtual environments and return their details."""
        root = root_path.resolve()
        venvs = []

        if self.verbose:
            with self.console.status("[cyan]Counting directories...", spinner="dots"):
                dirs_to_scan = list(root.rglob('*'))
                total_dirs = len(dirs_to_scan)
        else:
            dirs_to_scan = root.rglob('*')
            total_dirs = None

        with Progress(
            SpinnerColumn("dots"),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TextColumn("[dim cyan]{task.fields[path]}")
        ) as progress:
            scan_task = progress.add_task(
                "[cyan]Scanning directories...",
                total=total_dirs if self.verbose else None,
                path=""
            )

            for path in dirs_to_scan:
                progress.update(scan_task, advance=1, path=self.trim_path(str(path)))

                if path.is_dir() and self.is_virtualenv(path):
                    try:
                        size_mb = self.get_dir_size(path)
                        age_days = self.get_dir_age_days(path)

                        if older_than_days is None or age_days > older_than_days:
                            packages = self.get_venv_packages(path)
                            venv = VirtualEnv(
                                path=path,
                                size_mb=size_mb,
                                age_days=age_days,
                                is_broken=packages is None,
                                packages=packages
                            )
                            venvs.append(venv)
                    except Exception as e:
                        if self.verbose:
                            self.console.print(f"Warning: Error processing [bold yellow]{path}[/]: {e}")
                        continue

        if self.verbose:
            self.console.print(f"\n[green]Scan complete! Found {len(venvs)} virtual environments.")

        return venvs

    @staticmethod
    def remove_virtualenv(path: Path) -> bool:
        """Safely remove a virtual environment directory."""
        try:
            shutil.rmtree(path)
            return True
        except Exception as e:
            print(f"Failed to remove {path}: {e}", file=sys.stderr)
            return False

class VenvManager:
    """Class to manage virtual environment operations."""
    def __init__(self, console: Console, scanner: VenvScanner):
        self.console = console
        self.scanner = scanner

    def display_venv_info(self, venv: VirtualEnv, show_packages: bool = False):
        """Display information about a virtual environment."""
        self.console.print(f"\nPath: {venv.path}")
        self.console.print(f"Size: {venv.size_formatted} MB")
        self.console.print(f"Age: {venv.age_days} days")

        if venv.is_broken:
            self.console.print("VEnv: [bold red]broken[/]")
        else:
            self.console.print("VEnv: [bold cyan]ok[/]")
            if show_packages and venv.packages:
                self.console.print(f"\nInstalled packages:")
                for pkg in venv.packages:
                    self.console.print(f"  {pkg['name']} {pkg['version']}")

    def process_virtualenvs(self, root_dir: str, args):
        """Process virtual environments according to command line arguments."""
        try:
            venvs = self.scanner.scan_virtualenvs(Path(root_dir), args.older_than)

            if not venvs:
                self.console.print("No virtual environments found.")
                return

            broken_count = sum(1 for ve in venvs if ve.is_broken)
            total_size = sum(ve.size_mb for ve in venvs)

            for venv in venvs:
                self.display_venv_info(venv, args.list_packages)

                if venv.is_broken and args.remove_broken:
                    self.console.print("Removing broken venv...", end=" ")
                    if self.scanner.remove_virtualenv(venv.path):
                        self.console.print("[bold green]Done[/]")
                    else:
                        self.console.print("[bold red]Failed[/]")

            self.console.print(f"\nTotal virtual envs: {len(venvs)}")
            self.console.print(f"Broken virtual envs: {broken_count}")
            self.console.print(f"Total storage used: [bold green]{total_size:,.2f}[/] MB")

            if args.older_than and not args.remove:
                self.console.print("\nNote: This was a dry run. Use --remove to actually delete the virtual environments.")

        except Exception as ex:
            self.console.print(f"[bold red]Error: {ex}[/]", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Scan and manage Python virtual environments.')
    parser.add_argument('root_dir', help='Root directory to start scanning from')
    parser.add_argument('-v', '--verbose', action='store_true', help='Show additional scanning details')
    parser.add_argument('-p', '--list-packages', action='store_true', help='Show the list of packages installed in the virtual env')
    parser.add_argument('--older-than', type=int, help='Only show/remove virtual environments older than specified days')
    parser.add_argument('--remove', action='store_true', help='Remove virtual environments that match the criteria')
    parser.add_argument('--remove-broken', action='store_true', help='Remove identified broken virtual environments')
    return parser.parse_args()

def main():
    """Main entry point of the script."""
    args = parse_arguments()
    console = Console()
    scanner = VenvScanner(console, args.verbose)
    manager = VenvManager(console, scanner)

    if args.verbose:
        console.print(f"Scanning {args.root_dir} for virtual environments...")
        if args.older_than:
            console.print(f"Looking for environments older than [yellow]{args.older_than} days")

    manager.process_virtualenvs(args.root_dir, args)

if __name__ == "__main__":
    main()
