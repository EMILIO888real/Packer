## [%new_version] - %date

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

### Fixed
- Log file name.
- Streamed command output to log, no extra new lines.
- Some minor documentation inaccuracy's and other various changes that don't affect code.
- Stop tracking ignored __pycache__ files.
- input handling for the new `prompt_user` function in the description and version title generation.
- AI prompts to be more consistent cleaner and stricter. Specifically temperature, system and user prompts, limitations.
- Incorrect arhive path, using the version as a description, not the text.

---

## [0.1.0] - 2026.04.29

Initial release of packer, marking the first available version with core features and foundational functionality.
