## [%new_version] - %date

### Added
- `ui` folder with for now only a `tui.py` file, in the future there is a plan to create a `gui.py`.
- Git push to `change.py`, since it's better like this, user get's latests and it's fast enough.
- disabled echo for sensitive input via the python's built-in module and function `getpass`.
- `bool_answer` function that determines if a user's answer to a yes/no question is affirmative.
- `simple_prompt` function for much simpler cases of using `prompt_user` function since it was upgraded, for questions with y/n.
- *.github/workflows* tree.
- `build.yaml` file for building an exe for windows release of packer via github actions.
- `before_commands` and `after_commands` parameters to Packer class that execute custom shell commands before and after the git commit step. Commands are run in the repository directory using `sh -c` and are properly logged. This enables flexible automation like running tests, generating files, or deployment scripts at specific points in the release process.
- More correction on commit messages, by capitalizing them and removing trailing characters.
- A clean way to handle exceptions, especially keyboard interrupts.
- `main.spec` file creation and verification via running Pyinstaller for `setup.py`

### Changed
- Moved `create_go_file_folder` to `et`, since it used by a different module instead of just the main module.
- Moved `stripped_input` to `et`, same reason, used by a different module.
- Moved almost the entire `main` function that was inside `main.py` to `tui.py` as the new main functions there.
- Cleaned up some imports to not have extra unnceccery stuff and or circular imports.
- Reworked and significantly upgraded the `prompt_user` function.
- All `prompt_user` function calls to `simple_prompt` in `main.py`, since the prompts relied on the previous version, which now pretty much acts like `simple_prompt`.
- All necessary `prompt_user` function calls to `simple_prompt`, same reason as previous commit, outdated code.
- 0 and 1 around, instead of 0 being True and 1 being False, it's the opposite now.
- All instances of the name **Packer** to **packer**.
- Compile command to be more optional, moved in the correct spot.
- `setup.py` to also handle keyboardInterrupt exceptions and all other unexpected as well.
- Reorder some steps in `setup.py`
- Removed the redundant prompt for an already existing project creation.
- Cleaned up input in the `tui` module.
- Moved program name as the first input for a project creation and thanks to that there is an option to select a default project creation directory.
- Removed all safety and checks for creating a profile, since it's in `setup` and if the user already had a folder you don't create a new directory to just set settings.

### Fixed
- removed random extra argument for setup.
- Some `user_input` function calls to just `stripped_input`.

---

## [0.2.0] - 2026-05-07

### Added
- A safety check for uncommit git directory.
- option to add .gitignore exclusions to packer's exclusions.
- change.py to be able to quickly and easily add changes to your project.
- paths.py to be able to easily get paths to important packer files and directories cleanly and easily.
- A new way to log using the python's built-in logging module.
- A clean format version text function as per my preferred standart.
- Some extra simple safety checks.
- `setup.py` a function to create and setup a project in packer's format.
- an MIT license.
- A way to run setup.py directly.
- Documentation `for setup.py`.
- Auto filling setup.py entered data, like program name and github repo url, if not provided.
- Reading the .gitignore and using it's exclusions in the tree function, since now it supports patters.
- Pyinstaller to pyproject.toml, it is required by packer.
- For the new launch method a `main` function was added to `main.py`.

### Changed
- Logic for detecting a successful commit is more robust.
- Changed to correct src layout, by having the project name.
- Switched to use sys.exit instead of the placeholder's.
- Cleaned up the code a bit.
- Moved `prompt_user` function to et.
- Removed support for an git folder, now your project must be a git directory.
- Switched to using git to create an archive of your project for GoFile.
- Removed exclusions to packer, now git handles them exclusively.
- setup.py now returns the github repo url.
- All colors for reverting a version to yellow, instead of just white.
- `tree` function now hashes files and the root directory for more accurate project integrity, also removed support for zipfiles.
- The `tree` function in `et` now supports glob pattern matching for filenames, like **/__pycache__.
- The prompt for generating version description to not include ```.
- Removed creation and deletion of the temp project directory in favour of using git to create an archive.
- Pyinstaller is now run from path and has specific dedicated dist and build paths in the cache dir.
- Pyinstaller to be run using the Python executable that the script is ran from.
- Cleaned up some old and now unnceccery imports.
- pyproject.toml to be able to run the program with just `packer` after installation.
- Updated documentation to reflect all the changes and additions.

### Fixed
- Log file name.
- Streamed command output to log, no extra new lines.
- Some minor documentation inaccuracy's and other various changes that don't affect code.
- Stop tracking ignored __pycache__ files.
- input handling for the new `prompt_user` function in the description and version title generation.
- AI prompts to be more consistent cleaner and stricter. Specifically temperature, system and user prompts, limitations.
- Incorrect arhive path, using the version as a description, not the text.
- Updated `main.spec` to the new project structure, also fixed a lot of other random mistakes, essentially rewrote it.

---

## [0.1.0] - 2026.04.29

Initial release of packer, marking the first available version with core features and foundational functionality.
