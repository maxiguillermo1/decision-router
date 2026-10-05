# Practice lab drills

Pushing to this folder on `main` opens a **`[lab-drill]`** issue via **practice-lab-drill** workflow.

That issue automatically triggers:

1. **route-github-event** — cheap router comment (+ label when gates pass)
2. **consume-github-queue** — template or Cursor triage agent
3. Auto-close on the drill issue when the agent step finishes

Manual run: Actions → **practice-lab-drill** → pick scenario (`security`, `bug`, `spam`, `triage`, or `random`).

No artifact downloads or local commands required.
