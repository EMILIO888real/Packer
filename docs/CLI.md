Packer CLI
==========

Synopsis
--------

Invoke the CLI from the project virtual environment or any Python interpreter that can import `packer`.

If the package is installed (for example via `pip install .`), a console script entry point is provided and you can run `packer` directly:

```
packer [global options] [command] [command options]
```

You can still run the module form during development:

```
.venv/bin/python -m packer.main [global options] [command] [command options]
```

Global options
--------------

- `-p, --paths`  : Output all storage paths used by Packer.
- `-v, --version`: Display Packer's version.
- `-s, --saves`  : List saved project paths.
- `-c, --config` : Print current user configuration values.
- `--projects`   : Print saved project configurations.

Commands
--------

- `clear` : Remove generated data.
  - `-c, --cache` : Clear cache directory.
  - `-s, --save`  : Clear saved config/settings data.
  - `-l, --log`   : Clear log directory.
  - `-u, --user`  : Clear user data directory.
  - If no flags are provided, `clear` removes cache, config, data and logs.

- `run` : Run the release/update process for a saved project.
  - `-p, --project` : Project directory name (prompts if omitted).
  - `-v, --version` : Target version string (prompts if omitted).

- `edit` : Open user files in an editor.
  - `-s, --settings` : Open `settings.json` for editing.
  - `-p, --projects` : Open `projects.json` for editing.
  - `-t, --text_editor` : Override configured text editor.
  - `-w, --wait_flag`   : Override editor wait flag (e.g. `-w --wait` or `-w /wait`).

- `setup` : Run interactive project setup.
  - `-p, --path`        : Target project directory.
  - `-a, --author-name` : Author name for the new project.
  - `-n, --program-name`: Program name for the new project.
  - `-t, --pat`         : GitHub personal access token.
  - `-u, --github-url`  : GitHub repository URL.
  - `-o, --overwrite`   : Overwrite existing project files.

- `export` : Export Packer user config into an encrypted ZIP archive.
  - `-p, --path` : Destination directory for the archive.
  - `-s, --safe` : Password to encrypt the archive.

- `import` : Import Packer config from an archive.
  - `-p, --path` : Path to the archive to import (required).
  - `-s, --safe` : Password for the archive if encrypted.

Examples
--------

- Show help for the CLI:

```
packer --help
```


```
packer clear --cache --log
```


```
packer run --project myproject --version 1.2.3
```


```
packer edit --settings --projects
```


```
packer export --path /tmp --safe mypassword
```

Notes
-----

- The CLI uses the `settings.json` values for defaults such as `text_editor` and `wait_flag`.
- For development, run the module invocation from the repository root or activate the virtual environment first.
- Commands that prompt for input will use a stripped input helper to sanitize responses.
