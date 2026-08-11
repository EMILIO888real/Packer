Packer CLI
==========

Synopsis
--------

Invoke the CLI from a Python environment that can import `packer`.

If the package is installed, the console script entry point is available:

```bash
packer [global options] [command] [command options]
```

During development, you can also run the module form:

```bash
.venv/bin/python -m packer.main [global options] [command] [command options]
```

Many flags are optional and will prompt for input if they are not provided. Use `--help` to view the available options for the current command.

Global options
--------------

- `-p, --paths`  : Output all storage paths used by Packer.
- `-v, --version`: Display Packer's version.
- `-s, --saves`  : List saved project paths.
- `-c, --config` : Print the current user configuration values.
- `--projects`   : Print the saved project configurations.
- `-g, --gui`    : Launch the GUI interface.

Commands
--------

- `clear` : Remove generated data.
  - `-c, --cache` : Clear the cache directory.
  - `-s, --save`  : Clear saved config/settings data.
  - `-l, --log`   : Clear the log directory.
  - `-u, --user`  : Clear the user data directory.
  - If no flags are provided, `clear` removes cache, config, data and logs.

- `run` : Run the release/update process for a saved project.
  - `-p, --project` : Project directory name.
  - `-v, --version` : Target version string.

- `edit` : Open user-related files in an editor.
  - `-s, --settings` : Open `settings.json` for editing.
  - `-p, --projects` : Open `projects.json` for editing.
  - `-t, --text_editor` : Override the configured text editor.
  - `-w, --wait_flag`   : Override the editor wait flag (for example `--wait` or `/wait`).

- `setup` : Run interactive project setup.
  - `-p, --path`         : Target project directory.
  - `-a, --author-name`  : Author name for the new project.
  - `-n, --program-name` : Program name for the new project.
  - `-t, --pat`          : GitHub personal access token.
  - `-u, --github-url`   : GitHub repository URL.
  - `-o, --overwrite`    : Overwrite existing project files.
  - `-c, --code`         : GoFile URL or code (for example `OktQl5`).
  - `-l, --license`      : License for the new project.
  - `--authenticate`     : Authenticate with GitHub using a PAT for pushing.

- `export` : Export Packer user configuration into an encrypted ZIP archive.
  - `-p, --path` : Destination directory for the archive.
  - `-s, --safe` : Password used to encrypt the archive.

- `import` : Import Packer configuration from an archive.
  - `-p, --path` : Path to the archive to import.
  - `-s, --safe` : Password for the archive if it is encrypted.

- `change` : Commit a change for a Packer-style project.
  - `-p, --project` : Project directory name.
  - `-c, --changes` : Change description.
  - `-o, --overall-description` : Overall description of the change.
  - `-m, --ai-summary` : Disable AI summary generation.
  - `-s, --ai-suggestions` : Disable AI suggestion generation.

Examples
--------

Show help for the CLI:

```bash
packer --help
```

Clear cache and logs:

```bash
packer clear --cache --log
```

Run an update for a saved project:

```bash
packer run --project myproject --version 1.2.3
```

Open the settings and projects files in your editor:

```bash
packer edit --settings --projects
```

Export configuration to an archive:

```bash
packer export --path /tmp --safe mypassword
```

Launch the GUI:

```bash
packer --gui
```

Notes
-----

- The CLI uses the `settings.json` values for defaults such as `text_editor` and `wait_flag`.
- For development, run the module invocation from the repository root or activate the virtual environment first.
- Commands that prompt for input use a sanitized input helper to strip sensitive content from responses.
