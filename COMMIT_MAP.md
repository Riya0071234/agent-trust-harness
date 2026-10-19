# Commit map

On 2026-10-19, after all data had been collected and published, the history of `main` was rewritten once, only to remove the "Co-Authored-By" and session lines that the drafting assistant had appended to commit messages. Nothing else changed: every commit keeps its file contents (tree), author, date and subject. Because a commit ID depends on its message, every ID changed.

The original history, with the original IDs, is kept unchanged on the branch [`original-history`](https://github.com/Riya0071234/agent-trust-harness/tree/original-history). Every commit ID cited in `PREREG.md`, in the write-up and in each run's `manifest.json` refers to that branch, and the table below gives the matching commit on `main`. The tree column is the hash of the file contents, which is identical on both branches.

Check it yourself:

```bash
git log --reverse --format='%T %ad %s' --date=iso original-history > a.txt
git log --reverse --format='%T %ad %s' --date=iso main | head -n 21 > b.txt
diff a.txt b.txt        # prints nothing
```

| Original commit (cited in PREREG.md and manifests) | Commit on main | Tree (file contents) | Date (UTC) | Subject |
|---|---|---|---|---|
| f5c9afa | 249ed25 | a6a2560c478f | 2026-10-14 13:55 | Pre-registration, harness and tests, before any model run |
| b4d4c7a | 97020d3 | 7fe79c1c16b5 | 2026-10-14 13:57 | Pin model tiers and prices before the first real run |
| 20361f1 | 271bedf | 78780c7694ef | 2026-10-14 14:04 | Revision 2 before any model run: two vendors, credential wording fix, G4 |
| 6afae80 | 1812569 | b3a27a26f38a | 2026-10-19 06:37 | Pass temperature via extra_body for the Anthropic SDK; found in the smoke test, no prompt change |
| bc5c3e7 | 5df5221 | e28d34ec1504 | 2026-10-19 07:39 | Set reasoning_effort none for gpt-6-luna (required for function tools); log in PREREG |
| 193edee | d1f089b | 226ecb8faa71 | 2026-10-19 07:53 | Review fixes before the main runs: baseline cleaning, null-prediction rule, promise gap, resume safety, arm audit |
| 04d32e4 | 2efe4ca | 5e440b3d4f00 | 2026-10-19 07:53 | Record the commit in manifests from a zip copy via a GIT_COMMIT file |
| 43bbae3 | 3e98e6f | b0b646911cc2 | 2026-10-19 07:54 | Make the commit-fallback test valid inside a zip copy that has no .git |
| 6a1ec6a | 2fada0a | 49d198ad6f02 | 2026-10-19 07:58 | Retry appends locked by OneDrive, readable spend line, Windows setup and run scripts |
| 13e8fd5 | cebb9c3 | dcebc7d269cd | 2026-10-19 07:59 | Log run-robustness changes in PREREG |
| 532d93f | 6ad6cd0 | 7f40096119b2 | 2026-10-19 08:16 | Report the human-baseline study count actually used; log the Claude-only mechanics check |
| 869d40d | a2489c6 | c2d3987c6d9e | 2026-10-19 08:55 | Add cross-vendor pairs (buyer and supplier from different vendors); pre-register Experiment 3 before any such game |
| fe7bcc9 | b540588 | 432e973f3f3c | 2026-10-19 09:13 | Add Experiment 4 (stronger-model check) and the theory benchmark; pre-register both |
| 4f7bb2a | c8442f1 | 3215e62eb7e6 | 2026-10-19 10:40 | Fix gpt-6.1-sol: omit reasoning_effort when using function tools |
| 91cd341 | bc94a5c | 2d07d6ae5527 | 2026-10-19 11:04 | Refine gpt-6.1-sol fix: skip reasoning_effort for gpt-6.1 models entirely |
| abb504c | 72186f5 | acabbaa09cd1 | 2026-10-19 11:26 | Revert gpt-6.1-sol guesses in agents.py; add probe_sol.py to find the accepted request shape |
| ecb6cb6 | f8f84d2 | 62001f73dfaf | 2026-10-19 11:30 | Run gpt-6.1-sol through the Responses API (the only shape its live API accepted); log the deviation |
| 185fb54 | 39fca67 | c34d587e8d7e | 2026-10-19 11:55 | Record the model version each API returns; add MIT licence; document limits and next steps |
| 444484a | c486adf | 44c7b59ace51 | 2026-10-19 11:55 | Add raw transcripts and analyses for Experiments 1-4 (6,050 games, all audited) |
| 9f575a7 | 9445c02 | 5f6feb5fec7c | 2026-10-19 12:03 | Ignore console logs |
| eef6ed7 | 331a98c | ca91f5215919 | 2026-10-19 12:44 | Review fixes: manipulation check, measured SD, comprehension and verification tables, figures.py, reproduce script, CI, pinned requirements, tidier layout |
