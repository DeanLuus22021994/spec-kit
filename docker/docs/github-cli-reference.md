# GitHub CLI Reference

**Purpose**: Quick reference for commonly used GitHub CLI commands with correct field names and patterns.

## Repository Information

### Get Default Branch

```bash
# Correct field: defaultBranchRef (not defaultBranch)
gh repo view --json defaultBranchRef,nameWithOwner

# Output:
# {
#   "defaultBranchRef": {
#     "name": "semantic-foundation"
#   },
#   "nameWithOwner": "DeanLuus22021994/semantic-foundation"
# }
```

### Get Repository Details

```bash
# Common fields
gh repo view --json name,nameWithOwner,description,url,isPrivate,defaultBranchRef

# Full repository info
gh repo view
```

## Pull Requests

### List Pull Requests

```bash
# List all open PRs
gh pr list

# List PRs for specific branch
gh pr list --head docker-enhancements

# Get PR details as JSON
gh pr list --head docker-enhancements --json number,title,state,comments,reviews,url

# Common JSON fields for PRs:
# - number, title, state, url
# - author, assignees, reviewers
# - comments, reviews, reviewDecision
# - headRefName, baseRefName
# - createdAt, updatedAt, mergedAt
# - isDraft, mergeable, labels
```

### View Pull Request

```bash
# View current branch's PR
gh pr view

# View specific PR
gh pr view 123

# Open PR in browser
gh pr view --web

# Get PR as JSON
gh pr view --json number,title,state,reviews,comments
```

### Create Pull Request

```bash
# Interactive creation
gh pr create

# With title and body
gh pr create --title "feat: add new feature" --body "Description here"

# To specific base branch
gh pr create --base semantic-foundation --head docker-enhancements

# Draft PR
gh pr create --draft

# With assignees and labels
gh pr create --assignee @me --label enhancement,documentation
```

### Check PR Status

```bash
# Get CI/CD status checks
gh pr checks

# Get detailed view
gh pr view --json statusCheckRollup

# Watch for status changes
gh pr checks --watch
```

## Issues

### List Issues

```bash
# List open issues
gh issue list

# Filter by labels
gh issue list --label bug,priority-high

# Get as JSON
gh issue list --json number,title,state,labels,assignees
```

### Create Issue

```bash
# Interactive
gh issue create

# With details
gh issue create --title "Bug: Description" --body "Details" --label bug
```

## Workflow Actions

### List Workflows

```bash
# List all workflows
gh workflow list

# View specific workflow
gh workflow view

# View workflow runs
gh run list

# Watch latest run
gh run watch
```

### Trigger Workflow

```bash
# Trigger workflow
gh workflow run workflow-name.yml

# With inputs
gh workflow run workflow-name.yml -f environment=production
```

## Available JSON Fields

### Repository (`gh repo view --json`)

```
Core Fields:
  - nameWithOwner, name, owner
  - defaultBranchRef (not defaultBranch!)
  - description, url, sshUrl
  - isPrivate, isEmpty, isFork, isArchived

State:
  - createdAt, updatedAt, pushedAt
  - diskUsage, forkCount, stargazerCount

Settings:
  - hasIssuesEnabled, hasWikiEnabled
  - hasProjectsEnabled, hasDiscussionsEnabled
  - deleteBranchOnMerge
  - mergeCommitAllowed, squashMergeAllowed, rebaseMergeAllowed

Features:
  - languages, primaryLanguage
  - licenseInfo, codeOfConduct
  - repositoryTopics, labels

Access:
  - viewerPermission, viewerCanAdminister
  - viewerHasStarred, viewerSubscription
```

### Pull Request (`gh pr view --json`)

```
Identity:
  - number, title, url
  - headRefName, baseRefName
  - author, assignees, reviewers

State:
  - state, isDraft, mergeable, merged
  - createdAt, updatedAt, mergedAt, closedAt
  - reviewDecision, statusCheckRollup

Content:
  - body, comments, reviews
  - labels, milestone, projectCards

Files:
  - files, additions, deletions
  - changedFiles
```

### Issue (`gh issue view --json`)

```
Identity:
  - number, title, url
  - author, assignees

State:
  - state, stateReason
  - createdAt, updatedAt, closedAt

Content:
  - body, comments
  - labels, milestone, projectCards
```

## Common Patterns

### Check for Existing PR

```bash
# Check if PR exists for current branch
gh pr list --head $(git branch --show-current) --json number,state

# Exit code approach
if gh pr view --web 2>&1 | grep -q "no pull requests found"; then
    echo "No PR exists"
fi
```

### Get Current Branch Info

```bash
# Get current branch
git branch --show-current

# Check commits ahead of main
git log origin/main..HEAD --oneline

# Get default branch and check ahead
DEFAULT_BRANCH=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')
git log origin/$DEFAULT_BRANCH..HEAD --oneline
```

### Create PR with Auto-merge

```bash
gh pr create --title "feat: new feature" --body "Description" --base main --head feature-branch
gh pr merge --auto --squash
```

### Review PR Status

```bash
# Full PR status
gh pr view --json number,title,state,reviewDecision,statusCheckRollup,mergeable

# Just CI status
gh pr checks

# Comments and reviews
gh pr view --json comments,reviews
```

## Tips

1. **Always use `defaultBranchRef` not `defaultBranch`** when querying repo info
2. Use `--json` flag to get structured output for scripting
3. Use `--jq` to filter JSON: `gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'`
4. Check available fields with invalid field error (it lists all valid fields)
5. Use `gh <command> --help` to see all options
6. Use `gh auth status` to verify authentication

## Authentication

```bash
# Check auth status
gh auth status

# Login
gh auth login

# Switch accounts
gh auth switch

# Refresh token
gh auth refresh
```

---

**Last Updated**: 2025-11-24
**Reference**: [GitHub CLI Manual](https://cli.github.com/manual/)
