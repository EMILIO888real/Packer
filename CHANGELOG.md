## [%new_version] - %date

### Added
- 
- A prompt at the end of `tui` configuration for a new project whether to open `projects.json` in a text editor.

### Changed
- 
- The way `Packer` class checks modified, deleted and added files to use Git instead of utilizing the previous and new integrity.

### Fixed
- Git branch logic to update the origin (Github's) version of those branches.
- New version git tag landing on the same as the previous tag, now the tag is explicit attached to the latest commit vai sha.

---

## [0.6.0] - 2026-06-03

### Added
- settings parameter to Packer that allows more user related settings for controlling Packer behavior, they are optional extra options, by default Packer create's a Settings object with all the mandatory settings to `'None'`, they aren't checked there anyway.
- Option for verbosity via extra optional settings.
- Skip git status setting for skipping the safety check for a clean git directory, mostly for development purposes.
- Automatically suggest an author name, based on the logged in user name.
- Text editor choice to use the user settings if you launch `main` from `change.py`, instead of importing it.
- Optional way to edit the AI generated version description and or version title via the user's preferred text editor.
- The option to set your own version description prompts and or version title prompts for each of your projects.
- The option to run this project without any AI models, by providing `None` value instead of prompts to the constructor.
- Some helper functions to simplify `tui.py`: `check_module_conflict` and `print_list`.
- A helper function for prompting optional settings: `prompt_optional_setting` to reduce code complexity.
- All optional setting setting in the `TUI`, except for AI prompts.
- Input and output to logging.

### Changed
- Logging in `Packer` class to utilize the standart new in `et`.
- `capitalize` function in `et` to just capitalize the letter and not lower the rest of the characters.
- The entire save file architecture to use 2 setting files now instead of a single. One for saving project related settings, metadata, while the other saving Packer across all project, user settings.
- Removed `user_input` function, since it was buns.
- Packer classes default parameter values to use the `Project` classes default generated fields.
- Text for the files that open in the text editor, so it's simpler and more obvious what the user should do.
- Logic to handle differentiating between user and system prompts, assuming user uses only 2 role: user and role: system.
- Cleaned up `tui.py` main function to handle everything much easier.
- All IO interactions with the script, not the file system have been cleaned up a bit more by splitting them into more functions for simplicity.
- All inputs to utilize queues if they are provided.
- `setup` to not have any UI inputs, the only one there that was has been changed to a parameter for the `main` function.
- Git repo initiation for `Packer` to happen once in the constructor.
- Any encountered error's to be logged at the highest level.
- How logging Packer's IO happens, user interactions, surrounded the answer and the question with "" to be easier readable.
- Removed \n character at the start of the error IO for `Packer`.

### Fixed
- Packer implemented default UI to check for other settings, like `after_commands` and so on.
- A mistake in the `verbose` setting.
- Mistake in how the save files were handled in case of missing it, bound to have more error, since it is such a big architectural change.
- Another oversight regarding settings initialization for Packer, since now user interaction isn't necessary.
- Forgot to default the queues to None, since the `main` function in `main.py` uses a list of args approach to passing valus instead of kwargs.
- Fixed the version identifier to the correct version.
- Text editor opening after choosing a generated version description or title, by providing the path as a str instead if Path object.

---

## [0.5.0] - 2026-05-30

### Added
- Project script section to the new project created `pyproject.toml` file with a command to run the project's main file's main function after installing with `pip install -e .`.
- Automatic build file (executable) output validation via simply running it and looking for the correct output: "Hello, world!".
- Automatic git branch handling (Merging, creation and checkout).


### Changed
- `print_and_log` function to also be able to pass the `end` parameter to specify what type of str to attach to the end.
- Cleaned up the release notes to be more high level like the git commit message, by just using that for both.
- Various print function calls to also log and print it in a colorful way the output.
- return value and parameters in the `main` function of `setup.py` to allow not creating a Github repo.
- Added `pyproject.toml` file version identifier automatic updating via the excellent tomlkit module, that will preserve the file's structure.
- Newly created project version by `setup` to 0.0.0 instead of 0.1.0.
- All git interactions to utilize the excellent `GitPython` library.
- `revert_changes` method of `Packer`, since a lot of it's functionality wasn't useful, since it would have been automatically handled by Git anyways.
- `change.py` modules function to only capitalize the First letter and not make the rest of the letter Lower.
- Code location to have the user related stuff, like prompting more towards the beginning.
- Bundling and compilation to start running as soon as possible and print it out in an interactive way only when we are waiting on just that, otherwise it's only logged.
- `Git` add to utilize a whitelist of files to add instead of lazy staging via `git add .`, since it was causing a lot of problems.
- Added output to notify when the program is waiting for bundling and or compilation.
- `Git branch` automation logic to be a bit smarter, to correctly use weird states of the git repository and commit next version code boilerplate and other prep work.

### Fixed
- Mistakes in `setup.py` `main` function code parts for creating a new project's `main.py` and `paths.py` to actually use the user provided software name.
- Removed author from `pyproject.toml` file.
- Git branch deletion, to first switch to the main branch, since it isn't possible to delete the branch currently in use.
- Swapped the place of the code responsible for writing `CHANGELOG.md` new version's boilerplate code to happen after the branch, since otherwise git would discard changes.
- Merging logic to just always prefer "theirs" changes or the development branches version in case of conflict.
- `Git branch` logic and also changed it to run when it's needed, when you are on the development branch, otherwise skip it.

---

## [0.4.0] - 2026-05-27

### Added
- A public API for importing parts of the program.
- `utils` module for utilities and the `load_config` general function for loading and making settings available for the entire project.
- `simple_merge_settings` function to utils for easier standart settings merge.
- `normalize_settings_keys` function to `utils`, it changes whitespace " " to "_", to be able to be usable for python variables.
- Commit_version_summery generation via AI.
- `config.py` for centralized settings access by just import them.

### Changed
- `change.py` to be importable and cleaned it up a bit more to be easier to use, some basic things, like adding parameters and so on.>
- Ollama chat function call structure. nothing output wise changed.
- `load_config` to handle missing user settings, in that case it is None, just like default config.
- Refactored commit message to be easier editable in the future, cleaned it up.
- Settings to now use a Settings object for type and error checking via `pydantic.BaseModel`
- `all_settings` in `main.py` to now rely and use the object to access fields instead of a dict, since then the IDE can catch mistakes and check types
- `tui.py` to utilize the new `config.py`.
- `load_config` in `utils.py` to now check if user settings exists otherwise return None.
- Removed hidden imports from the newly created .spec file in the `setup.py` module.

### Fixed
- The minor mistake for checking if the commit message is generated to liking or not.
- Error not finding the correct project from the name alone, since the user only enters the program name not the entire path.

---

## [0.3.0] - 2026-05-16

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
- New program name safety checking to check if the name is valid for a python project.

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
- Updated the build.yaml file to use the new python standart for installing dependencies via `pip install -e .`, instead of `pip install -r requirements.txt`.

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
