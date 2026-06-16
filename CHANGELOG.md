## [%new_version] - %date

### Added
- `setup` command for the `CLI` to run the `setup` portion of Packer to create a new project, doesn't save it as a configuration mind you. 
- `core.py` to `setup` creation process for keeping all of user created packages main code. 
- `export` command to the CLI, which exports config saved by Packer to an archive, with the option to set a password, `--safe` and the path, `--path` to where. 
- Added an `import` command to the `CLI` to import archives that are the same style as the exported ones. 
- The function now generates an AI summary of the changes using an ollama model before writing it to a temporary file for user review. 
- 2 new prompts for generating the AI summaries have been added to `config.py`. 
- `CLI.md` for documenting various CLI commands and their uses cases as well as flags, more info available for each command using the --help or -h flag. 
- `SETTINGS.md` file to explain and showcase some `Packer` user related settings that aren't related to any specific project. 

### Changed
- `setup.py` logic for detecting whether the user has provided Github PAT or Github repo URL to be more flexible. 
- `revert_changes` method of the `Packer` class in `core.py` to handle cases where the user wants to revert after the entire run method has already ran, by cleaning up the git environment and now in a clean way. 
- `main.py` to import `core.py` main code to run in by calling it inside it's own `main` function, so that other parts of the software have access to it as well. 
- `--config` flag for the packer's CLI to look a bit better it's now a list with ": ", separating values with keys with each pair being on it's own line. 
- GoFile upload logic to be more robust, handle SSL verification errors and any other that arise with retry logic and pauses the release process after 3 retries, handles automatic reversion process. 
- `upload_gofile_file` function of `Packer` to not check errors on it's own, but simply raise an Exception if one occurs, since Packer already check for these. 
- `setup` `main` function's doctype to be more accurate to current state and added `ui` folder to it's creation. 
- Function `main` now accepts additional arguments: wait_flag, modification_types (default is ['c']), ai_summary (default is True), and verbose (default is True). 
- Function `which` is imported and used for finding the executable path of a text editor in the `CLI` module. 
- ompletely overhauled the README to use the same kind of structure that the `setup` generates as a README template. 
- `Project.md` file to also display the new `changelog_git_hash` settings field. 
- `changes_summary_prompt` to not include a negative prompt to not utilize multi level lists. 
- Modified README.md: Updates the link to the settings documentation from "docs/PROJECT.md" and "docs/CLI.md" to "docs/SETTINGS.md". The new link includes both global Packer settings and project-specific settings, while the old links only covered project-specific settings. 
- `revert changes` method of the `Packer` class now switches back to development branch, if it had switched to the master branch for git reversion. 
- Packer class's `revert_changes` method now accepts an optional parameter `exit` (default: True) to let the developer choose if they will exit them selves later after some clean up. 

### Fixed
- `setup`'s `exceptions.py` creation to write out ran \n characters inside the code instead of writing them out as actual new line chars. 
- The `revert_changes` function now handles deleting local git tag after updating origin (deleting remote tag) instead of the other way around. 

---

## [0.10.0] - 2026-06-14

### Added
- [8655170] `clear` command to clear user affected data by packer, like logs, cache, saves and so on. 
- [65c1af8] `exceptions.py` file creation to a new project's creation via `setup.py`. 
- [65c1af8] Rudimentary version of `config.py` to `setup` new project creation for `global_exception_handler` to work since it grabs the version of the project from there. 
- [48ad94e] `run` command to the `CLI` to able to run the project through just the CLI, without a TUI. 
- [48ad94e] `project_directory` parameter to the `Packer` class to be able to handle all directory changes and logic associated with like the git status command `Packer` itself. 
- [f07b4e8] `edit` command to open `settings.json` and `projects.json` from the `CLI` if wanted. 
- [9eb1001] Display commands for displaying both configurations saved by `Packer` `--config` and `--projects`. For `Packer` settings and for Packer saved projects.

### Changed
- [b2f287b] Moved updating the text editor setting with it's full path to config.py, so everyone(all modules in packer) can benefit from the update. 
- [8655170] Moved cli logic to a dedicated module `cli.py` in `ui` and import it into `main.py` as `tui`. 
- [65c1af8] Moved `exceptions.py` to `assets`, since it's a general purpose function for replacing the global_exception_handler, also won't probably change much. 
- [2c4d428] Moved logic to check whether bundled version functions as intended in `setup.py` to happen before committing, so it doesn't get committed. 
- [2c4d428] Added automatic removal for the `dist/` folder in a newly created project via `setup.py` and switched to an automatic only model, no human evaluation is needed anymore. 
- [b8327eb] Simplified `cli.py` `main` function to just exit at the end of the function, after running all possible commands for simpler architecture. 
- [5616db3] Next versions prepare commit to also utilize the same logic as the chore release commit, *sign it if possible*. 
- [48ad94e] Main class of the entire project `Packer` has been moved to `core.py`, to be available to any module in this project. 
- [48ad94e] `saves` command to not use internal resources and handle cases of first time boot up. 
- [48ad94e] `Packer` classes documentation to be up to date. 
- [c431d3c] `resolve_version` function has been moved to utils, since the same logic for input version str to be evaluated should work the same for `TUI` and `CLI`. 
- [c431d3c] `resolve_version` function to be a little less forgive and more flexible, but also strict. 
- [644a298] `run` command project specification to not be mandatory, if it isn't entered TUI launches. 
- [644a298] `run` commands `-n` `new_versions` parameter to not be mandatory, if missing launches TUI. 
- [9eb1001] Shorthand flags and the log flags for the `run` command to be simpler using the `dest` parameter for correct saving. 
- [9eb1001] All `edit` commands parameters shorthand and normal to be simpler with the `dest` parameter.

### Fixed
- [2c4d428] {} to {{}}, since otherwise they were accidentally being evaluated as f-string variables to inject during runtime. 
- [4f89972] Program exiting after parsing all parameters no matter what, even if there aren't any, a check now has been added.

---

## [0.9.0] - 2026-06-12

### Added
- [49a7212] Version output parameter to the CLI (-v, --version). 
- [f764fdf] A new module etf.py for python objects to help with terminal and various tui handling and configuration. *Module will be expended in the future using functions from et, since et is for more general stuff.*. 
- [056d2ac] `build.yaml` file creation to `setup.py`, with the updated syntax for creating a Windows exe of your program using Github Virtual machines via Github actions. 
- [5ae243e] A user setting for specify the `wait_flag` for GUI text editors and the ability to not use it for terminal based, like `nvim`.

### Changed
- [b28a252] Latest changelog for git releases to use the updated one with git hashes if it's in use. 
- [d5c7e09] `pyproject.toml` configuration to correctly build packer, now it functions with `pip install -e .` and `pip install .`. 
- [ab5feef] All file writing to utilize dedent with '''''' string blocks in `setup.py`, *not gonna lie, I prompted AI to change them*. 
- [f764fdf] Condensed the tui for setup into a function and moved it from tui.py to setup, since tui imports and setup can use it in case user chooses to run the module directly. 
- [f764fdf] Cleaned up the `tui` function in `setup.py` to be more flexible by allowing to create a project without a GitHub repo, just locally. 
- [056d2ac] Updated the `build.yaml` file to not utilize anymore, soon deprecated features, like the old asset uploading and the Node.js version. 
- [056d2ac] Updated all kinds of `setup.py` file creation and writing to use the latest packer tech for new projects, that includes upgrading the README, TODO.md and some other minor things. 
- [55e17fa] Updated documentation standart for `Sequence` object to use the one from `collections.abc`, instead of `typing` to support newer version. User had a problem like so: "TypeError: typing.Sequence[typing.Sequence] is not a generic class". 
- [490a4d3] `simple_merge_settings` to not allow None values for `user_settings`, ensuring the developer writes code with less bugs *hopefully*. 
- [44a9309] `before_commands` and `after_commands` to pre and post hooks, by allowing not only shell commands, but also callable object, like some function. 
- [c4421a0] Text editor path doesn't require to be resolved via shell, instead packer finds the full path using `shutil.which`.

### Fixed
- [516a91f] To utilize a different syntax for Sequence type notations: `Sequence[Sequence[str]]` instead of the old `Sequence[Sequence][str]`, because of the same user reported error. *If still ineffective will change to using a basic tuple*. 
- [2d1d720] The previous fix for the `Sequence` documentation didn't work, so it seems the library is flawed on some python env. in that case I have switched the 2 instances of Sequence using 2 notation to utilize tuples instead with the newer ellipsis syntax. 
- [e0db2f4] Minor mistake in the clean up of `setup's` `tui`, if user enters the GitHub token for creating a Repo on Github, it would crash, because of flawed logic. 
- [573d2d4] Minor mistake in `tui` module's `main` function, when I had moved the `tui` logic for `setup` to `setup.py`, I forgot to extract project directory individually in case user was creating one. 
- [728c7dc] Updated documentation in `config.py` to allow not using prompts, to skip AI generation and the `Sequence` documentation to tuple. 
- [b15e117] If the user settings file is missing it is created now instead of silently failing, by returning None value. 
- [b15e117] Updated flawed configuration merge logic to actually convert all settings to python acceptable and merge them correctly. 
- [c4421a0] Updated user settings loading to not only create the user settings file if missing, but also immediately return an empty dict, since otherwise it would fail and start to work after a restart.

---

## [0.8.0] - 2026-06-08

### Added
- [792ddfb] Git commits now try to be signed and if that fails, because of missing credentials them the commit is signed without.
- [e605790] Git fetching to fetch the Github release created tag to also be available in local git history.
- [f0dc942] Argument parsing for `main` function of packer using the ArgumentParser built-in module.
- [f0dc942] Paths or -p parameter to display all storage paths used by packer in case you want to delete, edit or view any of the files.
- [003e04e] Automatic changelog entry association with appropriate git commits. *Adds shortened git hash to each changelog entry*. 
- [032d98d] A setting to enable or disable automatic changelog entry association with the appropriate git commit, in case the users commits looks different than their changelog entries.

### Changed
- [f8dc718] `change.py` completely to now, also allow multiple changes and in the future AI generation.
- [627d374] Log file location output at the end of the script to contain it's own line.
- [f8dc718] `_just_log` to `_log_and_output_queue` to be able to easier see and if need parse output from packer by other programs, also disables verbosity automatically if using queues.
- [bcdcf75] `Packer` to not add the empty list lines to the template or boilerplate for the next version changelog.
- [eb71821] Packer's `main` function to use a simpler form of the packer's exclusive exception handler and to only assign it after packer's instance has been created.
- [d384590] Removed the date part in changelog additions, it will be replace with short git hash and it will be at the beginning instead of the end. 
- [04b77f6] Changed error report name to only contain the the date part. 
- [33d0797] `change.py` module's `tui` function to lower all changes in case user enters them as capital letters. 
- [33d0797] The name of a created issue to also only contain the date part.

### Fixed
- [f8dc718] `global_exception_handler` to now also handle external errors with grace, by checking if a log exists.
- [3e38e04] `change.py` to add all changes to changelog by updating it's internal changelog whenever it writes down a new entry.
- [792ddfb] `global_exception_handler` to allow weird states by checking if tmp_dir already exists.
- [5f71e1f] Git status via git diff to not show changes, if not git tags are available (like for the first version of a new project).
- [106a577] Minor mistake in the implementation of the git hashes for changelog entries, to write out the updated changelog. 
- [33d0797] Git tag fetching to use the wrapper. 
- [3dd001f] Correctly calculate the location of the start of the latest version's changelog. *But now I see, I could have done it in a much simpler way*.

---

## [0.7.0] - 2026-06-06

### Added
- A prompt at the end of `tui` configuration for a new project whether to open `projects.json` in a text editor.
- `global_exception_handler` to handle any uncaught exceptions, generate a report and create an issue archive.
- An exclusive exception handler for Packer itself to revert changes in case it was running, while the error occurred.
- A way to write your own release notes template using $syntax, a default is available as well.
- Documentation for project settings, how to set them and specific settings structure.

### Changed
- The way `Packer` class checks modified, deleted and added files to use Git instead of utilizing the previous and new integrity.
- `revert_changes` function, starts with `print_and_log`, since every use case was already manually doing it every time and also added to a call in case git didn't successfully commit.
- All user tied paths to be handled in `paths.py` and then just be imported by all parts of the program that needs them.
- Packer version to be stored in `config.py` and them imported by everyone.
- The release notes template to be a bit more standart and also included instructions for builds.

### Fixed
- Git branch logic to update the origin (Github's) version of those branches.
- New version git tag landing on the same as the previous tag, now the tag is explicit attached to the latest commit vai sha.
- Packer version to be a different version identifier than the project being updated.
- `global_exception_handler` to manually cast Path to str, since json tries to serialize it, but doesn't know how to.

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
