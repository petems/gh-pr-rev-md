## branch-squash

This is a workflow to allow the squashing of multiple commits on a single branch

## Git squash workflow
- Create backup branch: `git checkout -b {current-branch}-backup`
- Create squashed branch: `git checkout -b {current-branch}-squashed`
- Soft reset from main branch: `git reset --soft origin/main`
- Stage all changes: `git add .`
- Create single commit with proper formatting

## Commit message format
- Use semantic commit format: `<type>: <message title>`
- Title: lowercase, no period, max 50 characters
- Include body with bullet points explaining changes
- Limit to 4 bullet points maximum
- Focus on *why* changes were made, not just *what*

## Allowed commit types
- `feat`: New feature
- `fix`: Bug fix
- `chore`: Maintenance (tooling, dependencies)
- `docs`: Documentation changes
- `refactor`: Code restructure (no behavior change)
- `test`: Adding or refactoring tests
- `style`: Code formatting (no logic change)
- `perf`: Performance improvements

## Examples
```
feat(auth): add JWT login flow

- Implemented JWT token validation logic
- Added documentation for the validation component
```

```
refactor(api): split user controller logic

- Separated authentication and user management concerns
- Improved code maintainability and testability
```

## Lastly, next steps

DO NOT FORCE PUSH THIS BRANCH AS PART OF THIS WORKFLOW.

Document what the user could do next, but do not actually do the force push.

## Force Push Commands

```bash
# Method 1: Force push the current squashed branch to the original branch name
git push -f origin feat/main-{current-branch}-squashed:feat/main-{current-branch}

# Method 2: If you want to rename the current branch and force push
git branch -m feat/{current-branch}  # rename current branch
git push -f origin feat/{current-branch}  # force push to remote

# Method 3: Push with upstream setting
git push -f -u origin feat/{current-branch}-squashed:feat/{current-branch}
```

## What Each Command Does

- `-f` or `--force`: Forces the push even if it would overwrite existing commits
- `origin`: Your remote repository
- `{current-branch}-squashed:{current-branch}`: Pushes the squashed branch to the original branch name

## ⚠️ Important Safety Notes

Highlight this to to user:

1. __Force pushing rewrites history__ - Anyone who has pulled the original branch will need to reset their local copy
2. __Backup is preserved__ - Your `{current-branch}-backup` branch contains the original commit history
3. __Team coordination needed__ - Inform team members before force pushing if they have the original branch
4. __Current state__: Your branches appear to already be in sync based on the "Everything up-to-date" message

### Possible next steps

REMEMBER: Do not actually run these commands, merely suggest them as possible next steps.

```bash
# 1. Double-check you're on the right branch
git branch  # should show * {current-branch}-squashed

# 2. Verify the commit message is correct
git log --oneline -n 1

# 3. Force push to replace the original branch
git push -f origin {current-branch}-squashed:{current-branch}

# 4. Optional: Rename local branch to match
git branch -m {current-branch}

# 5. Optional: Set upstream for future pushes
git branch -u origin/{current-branch}
```


## General Guidelines
- Avoid vague titles like "update" or "fix stuff"
- Keep titles focused and under 50 characters
- Use bullet points for high-level summaries
- Ensure changes are logically grouped for squashing
- Always backup current branch before squashing
- Never do anything destructive without asking and highlighting to the user what it entails