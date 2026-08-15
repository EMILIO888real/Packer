# Manual Revert Instructions

If the automatic `revert_changes()` method fails, you can manually roll back the release by following these steps.

> **Note:** Values enclosed in `<...>` are placeholders. Replace them with the appropriate values and **do not** include the angle brackets (`<` and `>`) when running the commands.

## 1. Remove the generated archive

```bash
rm "<cache_dir>/<program_name>-<version>.zip"
```

To find the cache directory, run:

```bash
packer -p
```

Where:

* `cache_dir` is the directory reported by the command above.
* `program_name` is the name of your program.
* `version` is the version you were releasing.

---

## 2. Delete the uploaded Gofile archive

1. Go to https://gofile.io/.
2. Locate the uploaded archive.
3. Delete the archive matching the name of the local ZIP file you removed in the previous step.

---

## 3. Yank the uploaded PyPI release

If the project was published to PyPI, go to the project release management page:

```text
https://pypi.org/manage/project/<program_name>/releases/
```

Then:

1. Locate the uploaded release for `<version>`.
2. Yank or remove it through the PyPI web UI.
3. If the failed release left the project in a bad version state, bump the version in `pyproject.toml` to a post-release value such as `1.2.3.post1` or the next patch version, and commit it.

This matches the current rollback behavior in `revert_changes()`, which explicitly warns that PyPI distributions cannot be automatically yanked and instead updates the project version after a failed release.

---

## 4. Revert Git changes

First, determine how many release commits need to be removed.

```bash
git log --oneline
```

Find the latest commit created by the release process and count how many release commits should be rolled back.

If one or more commits need to be removed, reset the branch:

```bash
git reset --hard HEAD~<commit_count>
```

If the release process created commits on both the development and `master` branches, repeat the reset on both branches:

```bash
git checkout <branch_name>
git reset --hard HEAD~<commit_count>
```

Replace `branch_name` with the branch you want to reset.

---

## 5. Delete the GitHub release

1. Open your repository's **Releases** page.
2. Delete the release whose tag matches the released version.

---

## 6. Delete the remote Git tag

Delete the tag from the remote repository first:

```bash
git push origin :refs/tags/<version>
```

---

## 7. Delete the local Git tag

After the remote tag has been removed, delete the local tag:

```bash
git tag -d <version>
```

Where `version` is the same version used throughout this guide.
