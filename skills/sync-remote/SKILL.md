---
name: sync-remote
description: Amend the current commit with pertinent local changes, safely force-push its branch, and refresh the associated GitHub PR or GitLab MR description. Use when asked to amend and synchronize an existing review branch.
---

Synchronize the current review branch after follow-up edits. Infer GitHub versus GitLab from the branch's remote, amend only pertinent changes, push with an explicit force lease, and update the existing PR or MR description only when it became stale.

Invoking this skill explicitly authorizes amending `HEAD`, force-pushing the current branch, and editing its PR or MR description. Do not ask for separate confirmations. Stop and ask only when scope is ambiguous or a safety precondition fails.

## Preconditions and discovery

1. Confirm this is a Git worktree with a non-detached branch and at least one commit.
2. Resolve the current branch's configured upstream. Derive the remote name and remote branch from Git config; do not assume `origin` or that both branch names match:
   ```bash
   branch=$(git branch --show-current)
   remote=$(git config --get "branch.$branch.remote")
   merge_ref=$(git config --get "branch.$branch.merge")
   remote_branch=${merge_ref#refs/heads/}
   fetch_url=$(git remote get-url "$remote")
   mapfile -t push_urls < <(git remote get-url --push --all "$remote")
   ```
   Stop if any value is missing or the remote is `.`. This workflow is for an already-published branch.
3. Apply the non-overridable protected-branch guard before staging or amending anything:
   ```bash
   case "$branch" in
     main|master) echo "refusing to rewrite protected local branch: $branch" >&2; exit 1 ;;
   esac
   case "$remote_branch" in
     main|master) echo "refusing to rewrite protected remote branch: $remote_branch" >&2; exit 1 ;;
   esac
   ```
   Never amend or push when either name is `main` or `master`, even if that branch is not the remote default and even if the user asks to override this guard. Direct the user to create or check out a feature branch instead.
4. Normalize each URL to a canonical `<lowercase-host>/<repository-path-without-.git>` identity, accounting for HTTPS, `ssh://`, and SCP-style SSH syntax. Require exactly one push URL, set `push_url=${push_urls[0]}`, and require its canonical identity to equal the fetch identity. Protocol and username may differ. Stop on multiple push destinations or different fetch/push repositories; never let one invocation fetch, push, or edit reviews in different repositories. Keep the exact `push_url`, canonical identity, hostname, repository path, and a canonical HTTPS repository URL for all subsequent commands.
5. Parse the provider from the canonical hostname.
   - `github.com` selects `gh`.
   - `gitlab.com` selects `glab`.
   - For any other host, test that host with both available clients:
     ```bash
     gh auth status --hostname <host>
     glab auth status --hostname <host>
     ```
     Select the sole authenticated client that can resolve this repository. If both or neither qualify, ask whether the host is GitHub Enterprise or self-managed GitLab. Never choose merely because one binary is installed.
6. Check that the selected CLI exists and is authenticated for the remote host. Surface its error and stop if not; do not start an interactive login. Resolve the exact repository explicitly and verify the returned repository identity matches the canonical identity:
   - GitHub: `gh repo view "<host>/<repository-path>" --json nameWithOwner,url`
   - GitLab: `glab repo view "<canonical-HTTPS-URL>" --output json`

   Store that explicit selector as `repo_selector`. Pass `--repo "$repo_selector"` (GitHub) or `-R "$repo_selector"` (GitLab) to every subsequent review command; never rely on a CLI's current-directory repository inference.
7. Fetch only the exact upstream ref by URL, bypassing custom fetch mappings, then record `FETCH_HEAD`:
   ```bash
   git fetch --no-tags "$fetch_url" "refs/heads/$remote_branch"
   expected_oid=$(git rev-parse FETCH_HEAD)
   ```
   Continue only if the fetched tip equals `HEAD` or is an ancestor of `HEAD`. If the fetched branch is ahead of or diverged from local `HEAD`, stop and tell the user to reconcile it first. Never overwrite remote commits that are absent locally.
8. Refuse to amend any other remote default branch. After finding a review, also refuse if the current branch is its base/target branch. If `HEAD` is a merge commit, ask before amending because its intended diff is ambiguous.

## Find the review

Query the review associated with the current branch before changing anything. A missing review is allowed; it means the final description step is skipped.

- GitHub:
  ```bash
  gh pr view "$remote_branch" \
    --repo "$repo_selector" \
    --json number,title,body,url,baseRefName,headRefName,headRepository,headRepositoryOwner,isCrossRepository
  ```
- GitLab:
  ```bash
  glab mr view "$remote_branch" --repo "$repo_selector" --output json
  ```

If the source-repository query finds no review, search the provider for open reviews with the exact source repository and `remote_branch`; this covers reviews opened from forks. Require at most one match. Only after both lookups find nothing is there definitively no review.

Keep the review number/IID, URL, target repository selector, base/target branch, source repository and branch, and exact current description. Verify that the returned source repository and branch equal the configured upstream identity and `remote_branch`. Use the review's target repository selector and explicit number/IID for all later reads and edits. Authentication, authorization, network, and server errors are preflight failures and must stop the workflow.

## Select pertinent changes

Inspect all of the following:

```bash
git status --short
git diff
git diff --cached
git show --stat --format=fuller HEAD
if ! parent=$(git rev-parse --verify HEAD^ 2>/dev/null); then
  parent=$(git hash-object -t tree /dev/null)
fi
git diff "$parent" HEAD
```

Read untracked files that may belong to the change. Compare local edits with `HEAD`'s purpose and diff.

- Stage only changes that clearly complete, correct, test, or document the same logical change as `HEAD`.
- Do not treat already-staged files as automatically pertinent.
- Leave unrelated edits untouched, including their staged/unstaged state. Before unstaging a wholly unrelated path, save its exact cached binary patch to a temporary file. After amending (or after an amend failure), reapply it with `git apply --cached` and verify its cached diff exactly matches the saved patch. Stop rather than risk losing index state if it cannot be restored exactly.
- If a file mixes pertinent and unrelated hunks, stage only the pertinent patch when that can be done reliably. Otherwise ask the user which hunks belong.
- Never use `git add -A`, `git add .`, or another blanket staging command when unrelated changes exist.
- Do not run formatters that can modify unrelated files.

At amendment time, require the index to contain only pertinent changes. If pertinent and unrelated staged changes share a file or exact index restoration is uncertain, stop and ask instead of amending.

If no local changes are pertinent, continue: the commit message, push, or review description may still need synchronization. If there is nothing to change at any stage, finish as a no-op without rewriting `HEAD`.

## Amend `HEAD`

Review the combined commit that will result from the staged changes:

```bash
git diff --cached
git diff --cached "$parent"
git diff --cached "$parent" --stat
git log -1 --format=full
```

The `--cached` comparison against `parent` is the complete tree the amended commit will contain. Do not substitute a working-tree diff, which could include unrelated unstaged edits.

Amend only when pertinent staged changes exist or the existing message is inaccurate after considering the full resulting diff.

- Keep the message with `git commit --amend --no-edit` when it still describes the commit accurately.
- Otherwise write a concise message that describes the whole amended commit, not merely the latest edits, and amend with `git commit --amend -F -` using a quoted heredoc.
- Follow the repository's commit convention. Preserve issue-closing footers and other still-valid trailers.
- Do not add AI attribution.
- Do not bypass commit hooks with `--no-verify`.

Record the new `HEAD` object ID. If amendment fails, stop without pushing or editing the review.

## Push safely

Immediately before pushing, fetch the exact upstream ref by `fetch_url` again, read `FETCH_HEAD`, and verify it still equals `expected_oid`. If it changed, stop: another writer updated the branch after the preflight.

Re-run the protected-branch guard immediately before constructing the refspec. Abort if `branch` or `remote_branch` is `main` or `master`. Do not rely only on the earlier check: no code path may execute a push command whose destination is `refs/heads/main` or `refs/heads/master`.

If local `HEAD` already equals the remote tip, skip the push. Otherwise use an explicit force lease tied to the object ID inspected above:

```bash
git push \
  --force-with-lease="refs/heads/$remote_branch:$expected_oid" \
  "$push_url" \
  "HEAD:refs/heads/$remote_branch"
```

Never use `--force`, an unqualified `--force-with-lease`, `--no-verify`, or a push refspec that targets another branch. If the lease fails, do not retry until the remote change has been inspected and reconciled.

## Refresh the PR or MR description

After a successful push (or when no push was needed), compare the saved description with the complete branch diff and commit history against the review's base/target branch. Refresh the base/target ref or use the provider CLI's review diff so the comparison is not based on a stale local ref.

- Correct only content made stale or incomplete by the amended commit.
- Preserve accurate user-authored context, issue links, templates, checklists, screenshots, rollout notes, and testing instructions.
- Keep the repository's existing description structure. Do not regenerate the whole body just to normalize style.
- Do not change the review title, labels, reviewers, milestone, draft state, or target branch.
- If the description is still accurate, do not issue an edit command.
- Write a changed description to a temporary file and always remove it afterward.

Immediately before editing, fetch the review again by explicit number/IID and target repository. If its current description differs from the saved description, recompute the minimal update against the latest body. If concurrent edits overlap the proposed changes or cannot be merged confidently, stop without editing and report the conflict. If the latest body is already accurate, skip the edit.

Update only when necessary:

- GitHub:
  ```bash
  gh pr edit <number> --repo <target-repo-selector> --body-file <file>
  ```
- GitLab (the description flag accepts the file contents, not a filename):
  ```bash
  glab mr update <iid> --repo <target-repo-selector> \
    --description "$(cat <file>)" --yes
  ```

If the review update fails after the push, do not roll back or force-push again. Report that the branch is synchronized but the description still needs attention.

## Report

Return a compact summary containing:

- amended commit: old short SHA -> new short SHA, or `unchanged`
- commit message: `kept` or `updated`
- pushed branch and provider, or `already synchronized`
- PR/MR URL and description: `updated`, `already accurate`, or `not found`
- any unrelated local changes deliberately left untouched

Plain text only. No emojis.
