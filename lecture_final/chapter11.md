# **Chapter 11: Integration, Review & Final Presentation**

*A friendly guide to “putting it all together”*

You have written code that cleans data, draws charts, trains a model, and ships everything through a one-click deployment.  Great!  The last step in any real project—inside or outside university—is to **prove** that your work runs smoothly *and* tell a clear story about it.  This chapter walks you through the final two weeks:

1. **Integrate** every chapter’s piece into one repo and one Prefect workspace.
2. **Review** your own work and each other’s pull-requests.
3. **Present** a confident, five-minute live demo plus slides.

All tips are written for undergraduate students: no corporate buzzwords, just practical steps.

---

## 11.0 What “done” looks like

| Deliverable                                                                                                   | Where the grader will check |
| ------------------------------------------------------------------------------------------------------------- | --------------------------- |
| Git repo `dsi321` with ≥ 15 meaningful commits                                                                | GitHub commit list          |
| `README.md` ≥ 1 000 characters + build badge                                                                  | Repo home page              |
| One-command deployment (`docker compose up --build`)                                                          | Instructor runs locally     |
| Green CI check on last commit                                                                                 | GitHub Actions              |
| Prefect UI shows **three** scheduled deployments:<br> • `ingest-clean`<br> • `eda-pm25`<br> • `pm25-baseline` | Live during demo            |
| Flow-run artifacts: quality table, coverage plot, prediction plot                                             | Prefect “Artifacts” tab     |
| Slide deck (≤ 8 slides) in `slides/` folder                                                                   | Repo & presentation         |
| 5-minute live demo + 2-minute Q\&A                                                                            | Final session               |

---

## 11.1 Freeze the code (but not the data)

1. **Branch naming**

   * `dev` – keep hacking here
   * `release-candidate` – final polish
   * `main` – code that always works

2. When you open a pull-request from `release-candidate` into `main`, **check that CI passes**.

3. Tag the merge commit:

   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

---

## 11.2 Peer-review checklist (“LGTM” with meaning)

Before approving a teammate’s PR, answer **yes** to every line:

| ✓  | Question                                                   |
| -- | ---------------------------------------------------------- |
| ☐  | Does `ruff` or `flake8` show **zero** errors?              |
| ☐  | Do unit tests (`pytest`) pass?                             |
| ☐  | Can I run `docker compose up --build` and see Prefect UI?  |
| ☐  | Does the README explain how to trigger each flow?          |
| ☐  | Is there at least one screenshot or diagram in the README? |
| ☐  | Are secrets **not** included in the repo?                  |

If any box is unchecked, request changes—this is how software teams avoid last-minute fire drills.

---

## 11.3 Quality assurance “self-audit” script (optional but handy)

```python
# scripts/self_audit.py
from pathlib import Path

def check_figs():
    imgs = list(Path("figs").glob("*.png"))
    assert imgs, "No figures found in figs/"

def check_readme():
    txt = Path("README.md").read_text(encoding="utf-8")
    assert len(txt) > 1000, "README < 1000 chars"

def run():
    check_figs()
    check_readme()
    print("✅ Self-audit passed")

if __name__ == "__main__":
    run()
```

Run this locally before the PR; it saves you “Oops, forgot the plots!” moments.

---

## 11.4 Crafting the story: a slide-by-slide template

| Slide # | Content                               | Tip                                                   |
| ------- | ------------------------------------- | ----------------------------------------------------- |
| 1       | Title + team + one-sentence objective | “Predict hourly PM₂.₅ in Bangkok with open data”      |
| 2       | Why PM₂.₅ matters                     | One chart: WHO guideline vs Bangkok levels            |
| 3       | Pipeline diagram                      | Ingest → Clean → lakeFS → EDA → Model                 |
| 4       | Data quality snapshot                 | Table artifact: completeness & duplicates (all green) |
| 5       | Key EDA insight                       | Wind speed negative correlation plot                  |
| 6       | Model results                         | MAE, R², regression coefficients                      |
| 7       | Live demo checklist                   | bullets: start flow, show UI, show artifacts          |
| 8       | Next steps                            | e.g. random forest, deploy to cloud                   |

Keep text minimal; let charts speak.

---

## 11.5 Rehearsal: timing & backup

* Practice **click-path**:

  1. Open Prefect UI (bookmark).
  2. Trigger `ingest-clean` run -> show green.
  3. Click Artifacts tab, open plots.
  4. Open GitHub Actions page -> green check.

* Time yourself—talk ≤ 5 min.

* **Backup plan**: record a 1-minute GIF of the UI in case Wi-Fi fails.

---

## 11.6 Presentation day – 5 golden rules

1. **Start with the “why.”** The grader cares about impact, not just tech.
2. **Zoom, don’t scroll.** Show the exact UI element; audience won’t squint.
3. **Speak to humans.** Say “The model’s MAE is 8 µg/m³—good because WHO daily limit is 15.”
4. **Watch the clock.** A slide timer or phone on the lectern helps.
5. **Finish with thanks.** Invite questions confidently.

---

## 11.7 Rubric cross-walk table

Copy this into your README; the grader loves it.

| Rubric line         | Evidence in repo                                 |
| ------------------- | ------------------------------------------------ |
| ≥ 90 % completeness | `artifacts/summary.csv` & screenshots            |
| ≥ 5 commits/week    | GitHub insights graph                            |
| One-command run     | Video link + `docker-compose.prod.yml`           |
| ML used             | `flows/pm25_baseline.py`, `figs/pred_vs_obs.png` |

---

## 11.8 After the demo: retrospective

Set aside 10 minutes with your team:

1. **What went well?** (e.g., early data-quality checks saved time)
2. **What was hard?** (Docker cache issues?)
3. **One improvement for next time.**

Write three bullet points in `RETROSPECTIVE.md`—future you will thank you.

---

## 11.9 Key take-aways

* **Integration first, polish second.** A working, if ugly, pipeline beats a perfect but broken one.
* **Automate the boring stuff.** CI prevents “it works on my machine” excuses.
* **Tell a story.** Stakeholders remember clear visuals and numbers they can relate to.

You now have the full journey—from raw API call to nightly-retrained model—living in a public repo, with automated quality gates and a presentation you can proudly add to your portfolio.

**Congratulations!** 🎉 You’ve completed the course.  Keep the repo alive; future employers and research supervisors will love to see real, working data-engineering artefacts.
