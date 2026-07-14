# $program_name Update [$new_version]

$version_description

## Installation

Available via:

* **GitHub:** [GitHub Releases](https://github.com/${github_repo_url}/releases/tag/${new_version})
* **Third-party website (GoFile):** [Archive]($gofile_download_url) (click the download button).

### Binary Downloads

When downloading, please choose the correct build for your operating system:

| File Name | Platform | Description |
| --- | --- | --- |
| `$program_name` | Linux/macOS | Executable for Unix-based systems. |
| `$program_name.exe` | Windows | Executable for Windows systems. |

### To install:

* **GitHub:**
Download the appropriate binary for your system from the [Releases page](https://github.com/${github_repo_url}/releases/tag/${new_version}).
* **Third-party website (GoFile):**
Head to the website [Archive]($gofile_download_url) and download the specific arhive with the appropriate version.

After installing, continue following instructions via the README.

## Changes in $new_version

$latest_changelog

[Full changelog](https://github.com/${github_repo_url}/blob/master/CHANGELOG.md)

## Tips

If you prefer to build from source via **GitHub**, you can clone the repository using:

```bash
git clone https://github.com/${github_repo_url} --depth 1

```

Using `--depth 1` creates a "shallow clone," which only downloads the latest commit, saving you significant time and storage space compared to a full repository clone.

While downloading the pre-compiled binaries (like `$program_name` or `$program_name.exe`) is usually the fastest way to get started, cloning the repository allows you to easily pull future updates with `git pull` as they are released.

## Verification

To ensure the integrity of the downloaded files, you can verify their SHA256 checksums.

### How to verify:

* **Windows (PowerShell):**
Open PowerShell and run the following command:
```powershell
Get-FileHash .\$program_name.exe -Algorithm SHA256

```


* **Linux/macOS (Terminal):**
Open your terminal and run:
```bash
sha256sum $program_name

```

Compare the resulting hash with the one provided in the GitHub release assets list to ensure it matches.