# line-school-info
## Git

### Add & Commit

- `git add [file]`: Add files you want to include in the commit.
- `git commit -m "[commit message]"`: Commit the files you just added.

If you accidently add some files before commit, you can use `git rm --cached [file]`.

### Branch

- `git checkout [-b] [branch_name]`:
  - Add `-b` flag to create a new branch from current branch.
  - Or just move to the `HEAD` of `[branch_name]`.
- `git branch -m [old_branch] [new_branch]`: Change branch name.

### Push & Pull

First `checkout` to your working branch.

- `git push`: Push commits of a branch to remote (Github).
- `git pull`: Pull commits added by other users to local repository.

### Reset

- `git reset [commit hash]`: Remove commits after [commit hash], but preserves changes in local repository.
- `git reset --hard [commit hash]: Remove commits after [commit hash]. All changes made after [commit hash] are removed from both the branch history and the working directory, meaning these changes are lost and cannot be recovered.

### Revert commit

```
| commit abc (HEAD)
| commit def
```

`git revert HEAD` or `git revert abc` (`HEAD` is at commit `abc`)

After revert:

```
| commit ghi "revert abc" (HEAD)
| commit abc
| commit def
```

`git diff HEAD^^ HEAD` should produce no output.
