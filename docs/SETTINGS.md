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

The following options appear in the global `settings.json` file.

| Setting | Type | Default | Description |
| --- | --- | --- | --- |
| `text_editor` | `str` | `code` | The editor command Packer uses when opening files. Packer resolves this command with the system PATH. |
| `wait_flag` | `str \| None` | `--wait` | Optional flag appended to the editor command so Packer waits for the editor to close before continuing. Set to `null` to disable waiting. |
| `verbose` | `bool` | `true` | Enable more detailed runtime output from Packer. |
| `skip_git_status` | `bool` | `false` | Skip the pre-flight git status check before release and packaging operations. |
| `changes_summary_prompt` | `list[dict[str, str]]` | prompt template | Template used for AI-assisted summaries of git diffs. This is typically a system/user prompt pair. |
| `high_level_summary_prompt` | `list[dict[str, str]]` | prompt template | Template used to convert a bullet summary into one concise high-level sentence. |
| `model` | `str` | `mistral` | Default model name used for AI generation tasks in Packer. |
| `getpass_echo_char` | `str \| None` | `None` | Character used to echo input when prompting for passwords. Set to `null` to disable echoing. |
| `copy_github_release_clipboard` | `bool` | `true` | Copy the GitHub release URL to the clipboard after creating a release. |
| `open_gitHub_release` | `bool` | `true` | Open the GitHub release page in the default browser after creating a release. |
| `automatic_error_reporting` | `bool` | `true` | Automatically send error reports to the Packer developers for debugging purposes. |
| `desktop_notifications` | `bool` | `true` | Show desktop notifications for important events, such as release creation or errors. |

## Prompt settings

Two prompt settings are defined globally and can be customized in `settings.json`:

- `changes_summary_prompt`: controls how git diff summaries are generated.
- `high_level_summary_prompt`: controls how the bullet-point summary is converted into a short sentence.

These values are passed directly to the AI model and can be edited to adjust tone, style, or output structure.

## Notes

- These settings are global and apply to all Packer-managed projects for the current user.
- Project-specific settings such as `gofile_user_token`, `github_repo_url`, and `compile_command` are documented in `docs/PROJECT.md`.
- Changes to `settings.json` are loaded when Packer starts.

