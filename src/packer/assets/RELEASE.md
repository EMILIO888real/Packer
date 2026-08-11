# $program_name Update [$new_version]

$version_description

## Installation

Use the assets attached to this release page or PyPI to install this exact version.

### 1. Via PyPI
```bash
pip install ${pypi_program_name}==${new_version}
```

### 2. Via Attached Wheel File

Download `${program_name}-${new_version}-py3-none-any.whl` from the **Assets** section below, then run:

```bash
pip install ./${program_name}-${new_version}-py3-none-any.whl
```

### 3. From GoFile Source Archive

Download the source archive from [$gofile_download_url]($gofile_download_url) and install it locally with pip:

```bash
pip install /path/to/${program_name}-${new_version}.zip
```

### 4. Standalone Executable (No Python Required)

Download the binary for your platform from the **Assets** section below:

* **Linux:** `${program_name}` *(run `chmod +x ${program_name}` to make it executable)*
* **Windows:** `${program_name}.exe`

## Changes in $new_version

$latest_changelog

[Full changelog](https://github.com/${github_repo_url}/blob/master/CHANGELOG.md)

## Verification

To ensure the integrity of the downloaded files, you can verify their SHA256 checksums.

### How to verify:

* **Windows (PowerShell):**
Open PowerShell and run the following command:
```powershell
Get-FileHash .\$program_name.exe -Algorithm SHA256
```

* **Linux (Terminal):**
Open your terminal and run:
```bash
sha256sum $program_name
```

Compare the resulting hash with the one provided in the GitHub release assets list to ensure it matches.