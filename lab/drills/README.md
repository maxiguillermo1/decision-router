# Practice lab drills

Pushing to this folder on `main` opens a **`[lab-drill]`** issue via **practice-lab-drill** workflow.

The **practice-lab-drill** workflow then routes and runs the triage agent in the same job (GitHub does not fire `issues.opened` for issues created by `GITHUB_TOKEN`).

Human-opened issues still use **route-github-event** → **consume-github-queue**. Drill issues auto-close after the agent step.

Manual run: Actions → **practice-lab-drill** → pick scenario (`security`, `bug`, `spam`, `triage`, or `random`).

No artifact downloads or local commands required.
