# Python Virtual Environment Manager

A robust command-line tool for managing Python virtual environments. This tool
helps you scan, analyze, and clean up virtual environments across your system,
identifying broken or incompatible environments and managing disk space
effectively.

## Features

- 🔍 Recursive scanning of virtual environments
- 📊 Detailed size and age analysis
- 📦 Package listing for each environment
- 🔧 Detection of broken virtual environments
- 💻 CPU architecture compatibility checking
- 🧹 Automatic cleanup of invalid environments
- 📈 Progress tracking for large scans
- 🎨 Rich terminal output with color coding

## Requirements

- Python >= 3.13
- UV for dependency management and virtual env automated creation

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/venv-manager.git
cd venv-manager
```

2. Change file permission making it executable:
```bash
chmod +x venv-manager.py
```

That's all.

## Usage

Basic usage:

```bash
./venv-manager.py /path/to/scan
```

Available options:

```
Options:
  -v, --verbose        Show additional scanning details
  -p, --list-packages  Show the list of packages installed in each venv
  --older-than DAYS    Only show/remove virtual environments older than specified days
  --remove            Remove virtual environments that match criteria
  --remove-broken     Remove broken and architecture-incompatible environments
```

### Examples

1. Scan and show detailed information:

```bash
./venv-manager.py ~/projects -v
```

2. List all packages in found environments:

```bash
./venv-manager.py ~/projects -p
```

3. Find old virtual environments:

```bash
./venv-manager.py ~/projects --older-than 90
```

4. Remove broken or incompatible environments:

```bash
./venv-manager.py ~/projects --remove-broken
```

## Features in Detail

### Virtual Environment Detection

The tool identifies Python virtual environments by checking for standard markers:

- presence of `pyvenv.cfg`
- Python executable in `bin/` or `Scripts/`
- Site-packages directory

### Architecture Compatibility

The tool verifies that virtual environments match your system's CPU architecture by:

- Detecting the system's architecture
- Checking each virtual environment's Python executable
- Supporting common architectures (x86_64/amd64, arm64/aarch64)
- Identifying incompatible environments

### Status Categories

Virtual environments are classified as:

- ✅ Valid: Working and architecture-compatible
- ⚠️ Incompatible: Working but wrong architecture
- ❌ Broken: Not working or corrupted

## Output Example

```
Scanning /home/user/projects for virtual environments...

Path: /home/user/projects/project1/venv
Size: 156.42 MB
Age: 30 days
VEnv: ok
Architecture: x86_64 (compatible with system x86_64)
Installed packages:
  requests 2.31.0
  pandas 2.1.0

Path: /home/user/projects/project2/venv
Size: 89.15 MB
Age: 45 days
VEnv: incompatible architecture
Python arch: x86_64
System arch: arm64

Total virtual envs: 2
Broken virtual envs: 0
Incompatible architecture virtual envs: 1
Total storage used: 245.57 MB
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this code in your projects.

## Acknowledgments

- Rich library for beautiful terminal output
- UV for modern Python package management
