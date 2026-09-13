# Global Settings

This document describes the non-project-specific Packer settings stored in the user configuration file.
These settings are shared across all projects on the current machine and control general Packer behavior.

## File locations

Global settings are stored in the platform-specific Packer config directory.

| OS | Path |
| --- | --- |
| Linux | `~/.config/packer/settings.json` |
| macOS | `~/Library/Application Support/packer/settings.json` |
| Windows | `C:\Users\<username>\AppData\Local\EMILIO\packer\settings.json` |

## Settings

The following options are saved globally for all projects in `settings.json`.

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `text_editor` | `str` | `code` | Editor command Packer uses when opening files. It is resolved through the system PATH. |
| `wait_flag` | `str or None` | `--wait` | Optional flag appended to the editor command so Packer waits for the editor to close before continuing. Set to `null` if the editor is already blocking. |
| `verbose` | `bool` | `true` | Enable more detailed runtime output from Packer. |
| `skip_git_status` | `bool` | `false` | Skip the pre-flight git status check before release and packaging operations. |
| `changes_summary_prompt` | `list[dict[str, str]]` | prompt template | Template used for AI-assisted summaries of git diffs. This is typically a system/user prompt pair. |
| `high_level_summary_prompt` | `list[dict[str, str]]` | prompt template | Template used to convert a bullet summary into one concise high-level sentence. |
| `model` | `str` | `mistral` | Default model name used for AI generation tasks in Packer. |
| `getpass_echo_char` | `str or None` | `None` | Character used to echo input when prompting for passwords. Set to `null` to disable echoing. |
| `copy_github_release_clipboard` | `bool` | `true` | Copy the GitHub release URL to the clipboard after creating a release. |
| `open_gitHub_release` | `bool` | `true` | Open the GitHub release page in the default browser after creating a release. |
| `automatic_error_reporting` | `bool` | `true` | Automatically send error reports to the Packer developers for debugging purposes. |
| `desktop_notifications` | `bool` | `true` | Show desktop notifications for important events, such as release creation or errors. |
| `notification_sound_path` | `str or Path or None` | `'1'` | Path to a custom sound file for notifications, or one of the built-in preset names such as `1`, `2`, or `3`. |
| `notification_volume` | `float` | `1.0` | Volume for desktop notification sounds, from `0.0` (mute) to `1.0` (full volume). |
| `smooth_output` | `bool` | `true` | Enable smoother animated terminal output during long-running operations. |
| `smooth_output_speed` | `float` | `0.005` | Speed of the smooth output animation, in seconds per character. |
| `logs_size_threshold` | `int` | `104857000` | Maximum size of the logs directory in bytes before automatic cleanup is considered. default is `100 MiB` |
| `cache_size_threshold` | `int` | `1073741824` | Maximum size of the cache directory in bytes before automatic cleanup is considered. default is `1 GiB` |
| `auto_clear_cache` | `bool` | `false` | Automatically clear the cache when the cache size threshold is exceeded. |
| `auto_clear_logs` | `bool` | `true` | Automatically clear the logs directory when the logs threshold is exceeded. |
| `suggestions_prompt` | `list[dict[str, str]]` | prompt template | Prompt template used for generating short release-note-style suggestions from git diffs. |
| `stream_background_color` | `list[int] or None` | `[44, 44, 44]` | RGB color used as the background for streamed console output. |
| `window_resolution` | `list[int]` | `[800, 600]` | Resolution of the GUI window in pixels. |
| `window_background_color` | `list[int]` | `[13, 17, 23]` | RGB background color for the GUI window. |
| `slow_events` | `bool` | `true` | Whether to slow down event handling for smoother GUI performance. |
| `event_handler_speed` | `float` | `0.016` | Speed of event handling in seconds per update, approximately 60 UPS. |
| `gui_subsystem_speed` | `float` | `0.1` | Speed of GUI subsystem updates in seconds per update, approximately 10 UPS. |
| `window_fps` | `float` | `240` | Target frames per second for the GUI window. |
| `button_color` | `list[int]` | `[30, 30, 30]` | RGB color for GUI buttons. |
| `button_size` | `list[int | float]` | `[0.4, 0.08]` | Size of GUI buttons as a fraction of window size. |
| `vsync` | `bool` | `true` | Enable vertical synchronization for the GUI window. |
| `text_color` | `list[int]` | `[115, 115, 115]` | RGB color for text in the GUI. |
| `font_name` | `str or None` | `None` | Name of the font to use in the GUI. Set to `null` to use the system default. |
| `font_size` | `int` | `45` | Size of the font in the GUI. |
| `gui_exit_delay` | `float` | `3.0` | Delay in seconds before the GUI exits after a close event. |
| `compatibility` | `bool` | `true` | Enable GUI compatibility handling. On Windows, prints a compatibility notice and forces `slow_events` to `false`; currently has no effect on other systems. |

### GUI compatibility mode

When `compatibility` is `true`, Packer applies the compatibility behavior during GUI startup on Windows only. It displays a notice that compatibility settings are enabled and automatically disables `slow_events`. On Linux, macOS, and other systems, this setting currently does not change GUI behavior.

## Prompt settings

Three prompt settings are defined globally and can be customized in `settings.json`:

- `changes_summary_prompt`: controls how git diff summaries are generated.
- `high_level_summary_prompt`: controls how the bullet-point summary is converted into a short sentence.
- `suggestions_prompt`: controls how short release-note-style suggestion bullets are generated from a diff.

These values are passed directly to the AI model and can be edited to adjust tone, style, or output structure.

## Notes

- These settings are global and apply to all Packer-managed projects for the current user.
- Project-specific settings such as `gofile_user_token`, `github_repo_url`, `compile_command`, and `pypi_api_token` are documented in `docs/PROJECT.md`.
- Changes to `settings.json` are loaded when Packer starts.
