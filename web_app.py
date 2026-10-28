
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import shutil
import subprocess
import sys

app = FastAPI(title="ProofStack Studio")

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "verification_report.json"
CALCULATOR = ROOT / "sample_project" / "calculator.py"
PROJECT_DIR = ROOT / "sample_project"
BACKUP_DIR = ROOT / ".proofstack_backups"

# app.py resets this demo file to the same known-buggy baseline before each run.
BASELINE_SOURCE = """def calculate_total(price, discount):
    return price - discount
"""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ProofStack Studio</title>
<style>
:root {
  color-scheme: dark;
  --bg:#090e1b; --panel:#10182a; --panel2:#141e33;
  --line:#27334b; --text:#e8edf8; --muted:#92a0b9;
  --violet:#9875ff; --green:#4adea5; --red:#fb7185;
}
* { box-sizing:border-box }
body {
  margin:0; background:var(--bg); color:var(--text);
  font:14px/1.5 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;
}
button { font:inherit; cursor:pointer }
.topbar {
  height:72px; display:flex; align-items:center; justify-content:space-between;
  gap:16px; padding:0 28px; background:#0d1424;
  border-bottom:1px solid var(--line);
}
.brand { display:flex; align-items:center; gap:12px }
.logo {
  display:grid; place-items:center; width:38px; height:38px;
  border-radius:11px; background:linear-gradient(135deg,#a78bfa,#6d48e8);
  color:white; font-size:21px; font-weight:800;
}
.brand h1 { margin:0; font-size:18px; letter-spacing:-.5px }
.brand small { color:var(--muted); display:block; font-size:10px; letter-spacing:1.6px }
.pill {
  display:inline-flex; align-items:center; gap:7px; border:1px solid var(--line);
  border-radius:999px; padding:6px 10px; color:#cbd5e1; font-size:11px;
}
.dot { width:7px;height:7px;border-radius:50%;background:var(--green) }
main { max-width:1600px; margin:auto; padding:26px 28px 40px }
.eyebrow { color:#ae96ff; font-size:11px; font-weight:700; letter-spacing:1.8px }
.heading {
  display:flex; justify-content:space-between; align-items:flex-end;
  gap:18px; margin-bottom:24px;
}
.heading h2 { margin:5px 0 4px; font-size:27px; letter-spacing:-.9px }
.heading p { margin:0; color:var(--muted) }
.primary {
  background:var(--violet); border:1px solid #a78bfa; color:white;
  border-radius:10px; padding:11px 17px; font-weight:700;
  box-shadow:0 5px 24px #7550df25;
}
.primary:hover { background:#a78bfa }
.primary:disabled { opacity:.55; cursor:wait }
.metrics {
  display:grid; grid-template-columns:repeat(4,minmax(0,1fr));
  gap:14px; margin-bottom:18px;
}
.metric {
  background:var(--panel); border:1px solid var(--line);
  border-radius:13px; padding:16px;
}
.metric-label { color:var(--muted); font-size:11px; letter-spacing:.7px }
.metric-value { margin-top:6px; font-size:21px; font-weight:750; overflow-wrap:anywhere }
.metric-note { margin-top:3px; color:var(--muted); font-size:11px }
.workspace {
  display:grid; grid-template-columns:minmax(0,1.15fr) minmax(0,1fr);
  gap:16px; align-items:start;
}
.panel {
  min-width:0; overflow:hidden; background:var(--panel);
  border:1px solid var(--line); border-radius:14px;
}
.panel-head {
  min-height:57px; padding:14px 17px; display:flex; align-items:center;
  justify-content:space-between; gap:12px; border-bottom:1px solid var(--line);
}
.panel-title { font-weight:700; font-size:13px }
.panel-sub { color:var(--muted); font-size:11px; margin-top:2px }
.filetag {
  border:1px solid var(--line); border-radius:7px; padding:4px 8px;
  font-size:11px; color:#c4b5fd;
}
.editor { padding:16px 0; background:#0b1221; overflow-x:auto }
.code {
  display:grid; grid-template-columns:38px minmax(max-content,1fr);
  font:12px/2.05 ui-monospace,SFMono-Regular,Consolas,monospace;
  white-space:pre; padding-right:16px;
}
.ln { text-align:right; color:#53617b; padding-right:13px; user-select:none }
.src { color:#d6def0 }
.kw { color:#c4a7ff }
.fn { color:#7dd3fc }
.str { color:#a7e3b1 }
.badline { background:#49222f; color:#fda4af; display:block; padding:0 10px }
.goodline { background:#12372f; color:#86efac; display:block; padding:0 10px }
.editor-note { padding:11px 16px; border-top:1px solid var(--line); color:var(--muted); font-size:11px }
.comparison { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:1px; background:var(--line) }
.compare-pane { min-width:0; background:#0b1221 }
.compare-head { display:flex; align-items:center; justify-content:space-between; gap:8px; padding:10px 12px; border-bottom:1px solid var(--line); font-size:11px; font-weight:750 }
.compare-label { display:inline-flex; align-items:center; gap:6px }
.compare-mark { width:7px; height:7px; border-radius:50%; background:var(--red) }
.compare-mark.good { background:var(--green) }
.diff-code { margin:0; padding:12px 0; max-height:380px; overflow:auto; white-space:pre; overflow-wrap:normal; font:11px/1.8 ui-monospace,SFMono-Regular,Consolas,monospace; color:#d6def0 }
.diff-line { display:block; min-width:max-content; padding:0 12px 0 10px }
.diff-line.changed-old { background:#49222f; color:#fda4af }
.diff-line.changed-new { background:#12372f; color:#86efac }
.diff-line .number { display:inline-block; width:25px; margin-right:10px; text-align:right; color:#53617b; user-select:none }
.diff-empty { color:var(--muted); padding:14px; font-size:11px }
.section { padding:16px }
.form-grid { display:grid; grid-template-columns:minmax(0,1fr); gap:12px }
.field-label { display:block; color:var(--muted); font-size:11px; font-weight:750; margin-bottom:6px }
select, textarea {
  width:100%; color:var(--text); background:#0b1221; border:1px solid var(--line);
  border-radius:9px; padding:10px 11px; font:12px/1.5 ui-monospace,SFMono-Regular,Consolas,monospace;
}
textarea { min-height:88px; resize:vertical; font-family:inherit }
.secondary { background:#1a2540; border:1px solid var(--line); color:var(--text); border-radius:9px; padding:9px 13px; font-weight:700 }
.secondary:disabled { opacity:.55; cursor:wait }
.form-note { color:var(--muted); font-size:11px; margin-top:7px }

.section-label { color:var(--muted); font-size:10px; letter-spacing:1.2px; font-weight:750; margin-bottom:10px }
.resultbox {
  background:#0b1221; border:1px solid var(--line); border-radius:10px;
  padding:13px; margin-bottom:12px; min-width:0;
}
.result-top { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:8px }
.status {
  display:inline-block; border-radius:6px; padding:4px 7px;
  background:#17382f; color:#86efac; font-size:10px; font-weight:800;
}
.status.fail { background:#48212d; color:#fda4af }
.status.pending { background:#292444; color:#c4b5fd }
pre {
  white-space:pre-wrap; overflow-wrap:anywhere; margin:0;
  color:#aab8d0; font:11px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;
  max-height:230px; overflow:auto;
}
.empty { color:var(--muted); font-size:12px; padding:8px 0 }
.ledger { margin-top:16px }
.ledger-body { padding:16px }
.ledger-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:12px }
.ledger-item { border:1px solid var(--line); border-radius:10px; padding:13px }
.ledger-item b { display:block; font-size:12px; margin-bottom:5px }
.ledger-item span { color:var(--muted); font-size:11px; overflow-wrap:anywhere }
.footer { padding-top:20px; color:#66748e; font-size:11px; text-align:center }
#notice { color:var(--muted); font-size:12px; margin-top:10px; min-height:18px }
@media(max-width:900px) {
  main { padding:20px 15px }
  .topbar { padding:0 15px }
  .workspace { grid-template-columns:1fr }
  .metrics { grid-template-columns:repeat(2,minmax(0,1fr)) }
  .ledger-grid { grid-template-columns:1fr }
  .comparison { grid-template-columns:1fr }
  .heading { align-items:flex-start; flex-direction:column }
}
@media(max-width:440px) {
  .pill { display:none }
  .metric { padding:12px }
  .metric-value { font-size:17px }
}
</style>
</head>
<body>
<header class="topbar">
  <div class="brand">
    <div class="logo">P</div>
    <div><h1>ProofStack</h1><small>AI REPAIR WORKSPACE</small></div>
  </div>
  <div class="pill"><span class="dot"></span> API configured · NVIDIA</div>
</header>

<main>
  <div class="heading">
    <div>
      <div class="eyebrow">DEVELOPER WORKSPACE / OVERVIEW</div>
      <h2>Repair. Verify. Prove.</h2>
      <p>AI-proposed code repairs, validated by automated tests.</p>
    </div>
    <div>
      <button id="runBtn" class="primary" onclick="runRepair()">▶ &nbsp; Run repair &amp; verify</button>
      <div id="notice" role="status"></div>
    </div>
  </div>

  <section class="metrics">
    <div class="metric"><div class="metric-label">ACTIVE MODEL</div>
      <div class="metric-value" id="modelMetric">Nemotron</div>
      <div class="metric-note">NVIDIA API inference</div></div>
    <div class="metric"><div class="metric-label">BEFORE REPAIR</div>
      <div class="metric-value" id="beforeMetric">—</div>
      <div class="metric-note">Baseline test run</div></div>
    <div class="metric"><div class="metric-label">AFTER REPAIR</div>
      <div class="metric-value" id="afterMetric">—</div>
      <div class="metric-note">Post-patch test run</div></div>
    <div class="metric"><div class="metric-label">VERIFICATION</div>
      <div class="metric-value" id="statusMetric" style="font-size:15px">Awaiting run</div>
      <div class="metric-note">Determined by pytest</div></div>
  </section>

  <section class="workspace">
    <article class="panel">
      <div class="panel-head">
        <div><div class="panel-title">Source workspace</div>
          <div class="panel-sub">Known demo bug · calculator.py</div></div>
        <span class="filetag">PYTHON</span>
      </div>
      <div class="comparison">
        <section class="compare-pane">
          <div class="compare-head"><span class="compare-label"><span class="compare-mark"></span> ORIGINAL</span><span class="filetag">BASELINE</span></div>
          <pre id="originalCode" class="diff-code"><span class="diff-empty">Run repair to load original source.</span></pre>
        </section>
        <section class="compare-pane">
          <div class="compare-head"><span class="compare-label"><span class="compare-mark good"></span> REPAIRED</span><span class="filetag">NEMOTRON</span></div>
          <pre id="repairedCode" class="diff-code"><span class="diff-empty">Actual model output appears here after the run.</span></pre>
        </section>
      </div>
      <div class="editor-note">Line highlights show changed or added lines. The repaired pane displays the source written by the repair pipeline.</div>
      <div class="section">
        <div class="section-label">CUSTOM REPAIR</div>
        <div class="form-grid">
          <div>
            <label class="field-label" for="targetFile">Python file inside sample_project</label>
            <select id="targetFile"><option value="calculator.py">calculator.py</option></select>
          </div>
          <div>
            <label class="field-label" for="repairTask">What should ProofStack fix?</label>
            <textarea id="repairTask" placeholder="Example: Fix the fractional discount calculation. discount is a fraction between 0 and 1.">Fix the fractional discount calculation. The discount is a fraction between 0 and 1, so calculate price * (1 - discount).</textarea>
          </div>
          <div>
            <button id="customRunBtn" class="secondary" onclick="runCustomRepair()">Run custom repair &amp; verify</button>
            <div class="form-note">A timestamped backup is created before the target file is changed. Pytest runs against sample_project before and after the proposed repair.</div>
          </div>
        </div>
        <div class="section-label" style="margin-top:18px">DEMO PIPELINE</div>
        <div class="resultbox">
          <div class="panel-title">Fix fractional discount calculation</div>
          <div class="panel-sub">The demo button still runs the original calculator scenario. Custom repairs use the selected source file and save a timestamped backup.</div>
        </div>
        <div class="section-label">RUN PIPELINE</div>
        <div class="panel-sub">01 &nbsp; Baseline tests → 02 &nbsp; Model proposal → 03 &nbsp; Apply patch → 04 &nbsp; Verify with pytest</div>
      </div>
    </article>

    <article class="panel">
      <div class="panel-head">
        <div><div class="panel-title">Verification console</div>
          <div class="panel-sub">Execution evidence from the latest run</div></div>
        <span id="overallStatus" class="status pending">NOT RUN</span>
      </div>
      <div class="section">
        <div class="section-label">BEFORE REPAIR · BASELINE</div>
        <div class="resultbox">
          <div class="result-top"><span class="panel-title">pytest output</span>
            <span id="beforeBadge" class="status pending">PENDING</span></div>
          <pre id="beforeOutput">Run the repair pipeline to collect baseline test evidence.</pre>
        </div>
        <div class="section-label">AFTER REPAIR · VERIFICATION</div>
        <div class="resultbox">
          <div class="result-top"><span class="panel-title">pytest output</span>
            <span id="afterBadge" class="status pending">PENDING</span></div>
          <pre id="afterOutput">The proposed fix has not been verified yet.</pre>
        </div>
      </div>
    </article>
  </section>

  <section class="panel ledger">
    <div class="panel-head">
      <div><div class="panel-title">Evidence ledger</div>
        <div class="panel-sub">Provenance and limitations for the current run</div></div>
      <span class="filetag">JSON REPORT</span>
    </div>
    <div class="ledger-body">
      <div class="ledger-grid">
        <div class="ledger-item"><b>Inference provider</b><span id="providerInfo">NVIDIA API · not Nebius</span></div>
        <div class="ledger-item"><b>Model identifier</b><span id="modelInfo">Loaded from latest report</span></div>
        <div class="ledger-item"><b>Evidence artifact</b><span>verification_report.json</span></div>
      </div>
      <div class="resultbox" style="margin-top:12px;margin-bottom:0">
        <div class="section-label">VERIFICATION DETAILS</div>
        <pre id="limitations">No report loaded yet. Run the pipeline to see recorded limitations.</pre>
      </div>
      <div class="resultbox" style="margin-top:12px;margin-bottom:0">
        <div class="result-top">
          <span class="panel-title">Full evidence report</span>
          <a class="filetag" href="/api/report/download" style="text-decoration:none">Download JSON</a>
        </div>
        <pre id="rawReport">Run the pipeline to load the complete verification_report.json.</pre>
      </div>
    </div>
  </section>
  <div class="footer">ProofStack Studio · Test evidence, not a guarantee of complete correctness.</div>
</main>

<script>
function setText(id, value) {
  document.getElementById(id).textContent = value ?? "—";
}
function setBadge(id, label, kind) {
  const el = document.getElementById(id);
  el.textContent = label;
  el.className = "status" + (kind ? " " + kind : "");
}
function testSummary(test) {
  if (!test) return "—";
  const text = test.output || "";
  const passedMatch = text.match(/(\d+) passed/);
  const failedMatch = text.match(/(\d+) failed/);
  if (passedMatch || failedMatch) {
    const passed = passedMatch ? passedMatch[1] : "0";
    const failed = failedMatch ? failedMatch[1] : "0";
    return passed + " passed · " + failed + " failed";
  }
  return test.passed ? "Passed" : "Failed";
}
function renderCodeComparison(originalSource, repairedSource) {
  const original = String(originalSource || "").replace(/\\r/g, "").replace(/\\n$/, "").split("\\n");
  const repaired = String(repairedSource || "").replace(/\\r/g, "").replace(/\\n$/, "").split("\\n");
  // LCS-based diff: mark unchanged lines normally and changed/added lines clearly.
  const rows = original.length + 1;
  const cols = repaired.length + 1;
  const dp = Array.from({length: rows}, () => Array(cols).fill(0));
  for (let i = original.length - 1; i >= 0; i--) {
    for (let j = repaired.length - 1; j >= 0; j--) {
      dp[i][j] = original[i] === repaired[j]
        ? dp[i + 1][j + 1] + 1
        : Math.max(dp[i + 1][j], dp[i][j + 1]);
    }
  }
  const oldChanged = new Set();
  const newChanged = new Set();
  let i = 0, j = 0;
  while (i < original.length || j < repaired.length) {
    if (i < original.length && j < repaired.length && original[i] === repaired[j]) {
      i++; j++;
    } else if (j < repaired.length && (i === original.length || dp[i][j + 1] >= dp[i + 1][j])) {
      newChanged.add(j++);
    } else if (i < original.length) {
      oldChanged.add(i++);
    }
  }
  const paint = (id, lines, changed, className) => {
    const target = document.getElementById(id);
    target.replaceChildren();
    lines.forEach((line, index) => {
      const row = document.createElement("span");
      row.className = "diff-line" + (changed.has(index) ? " " + className : "");
      const number = document.createElement("span");
      number.className = "number";
      number.textContent = String(index + 1).padStart(2, "0");
      row.append(number, document.createTextNode(line || " "));
      target.append(row);
    });
  };
  paint("originalCode", original, oldChanged, "changed-old");
  paint("repairedCode", repaired, newChanged, "changed-new");
}

async function loadProjectFiles() {
  const select = document.getElementById("targetFile");
  try {
    const response = await fetch("/api/files");
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Could not list project files");
    select.replaceChildren();
    (data.files || []).forEach(file => {
      const option = document.createElement("option");
      option.value = file;
      option.textContent = file;
      select.append(option);
    });
    if (!data.files || data.files.length === 0) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "No eligible Python files found";
      select.append(option);
    }
  } catch (error) {
    setText("notice", "Could not load Python files: " + error.message);
  }
}

async function runCustomRepair() {
  const button = document.getElementById("customRunBtn");
  const target = document.getElementById("targetFile").value;
  const task = document.getElementById("repairTask").value.trim();
  if (!target) {
    setText("notice", "Choose a Python source file inside sample_project.");
    return;
  }
  if (!task) {
    setText("notice", "Enter a repair instruction first.");
    return;
  }
  button.disabled = true;
  button.textContent = "Repairing and verifying…";
  setText("notice", "Creating a backup, asking Nemotron for a patch, and running pytest…");
  setBadge("overallStatus", "RUNNING", "pending");
  try {
    const response = await fetch("/api/run-custom", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({target_file: target, task: task})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Custom repair failed");
    const report = data.report || {};
    renderCodeComparison(data.original_source || "", data.repaired_source || "");
    setText("rawReport", JSON.stringify(report, null, 2));
    setText("beforeOutput", report.before?.output || "No baseline output recorded.");
    setText("afterOutput", report.after?.output || "No post-repair output recorded.");
    setText("beforeMetric", testSummary(report.before));
    setText("afterMetric", testSummary(report.after));
    setText("statusMetric", report.verification_status || "Unknown");
    setText("modelInfo", report.model || report.model_adapter || "Not recorded");
    setText("providerInfo", report.mode || "Provider not recorded");
    setText("limitations", (report.limitations || []).map(x => "• " + x).join("\n") || "No limitations recorded.");
    setBadge("beforeBadge", report.before?.passed ? "PASSED" : "FAILED", report.before?.passed ? "" : "fail");
    setBadge("afterBadge", report.after?.passed ? "PASSED" : "FAILED", report.after?.passed ? "" : "fail");
    const verified = report.verification_status === "VERIFIED_TESTS_PASS";
    setBadge("overallStatus", verified ? "TESTS PASS" : "CHECK RESULTS", verified ? "" : "fail");
    setText("notice", (verified ? "Custom repair verified. " : "Custom repair finished; inspect test output. ") +
      "Backup: " + (report.backup || "recorded in report"));
  } catch (error) {
    setBadge("overallStatus", "ERROR", "fail");
    setText("notice", "Custom repair error: " + error.message);
  } finally {
    button.disabled = false;
    button.textContent = "Run custom repair & verify";
  }
}
document.addEventListener("DOMContentLoaded", loadProjectFiles);

async function runRepair() {
  const button = document.getElementById("runBtn");
  button.disabled = true;
  button.textContent = "Running pipeline…";
  setText("notice", "Calling the repair pipeline and collecting test evidence…");
  setBadge("overallStatus", "RUNNING", "pending");
  try {
    const response = await fetch("/api/run", {method:"POST"});
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Pipeline request failed");

    if (!data.report) {
      throw new Error(data.detail || data.console_output || "The pipeline did not produce a verification report.");
    }
    const report = data.report;
    renderCodeComparison(data.original_source || "", data.repaired_source || "");
    setText("rawReport", JSON.stringify(report, null, 2));
    setText("beforeOutput", report.before?.output || "No baseline output recorded.");
    setText("afterOutput", report.after?.output || "No post-repair output recorded.");
    setText("beforeMetric", testSummary(report.before));
    setText("afterMetric", testSummary(report.after));
    setText("statusMetric", report.verification_status || "Unknown");
    setText("modelInfo", report.model || report.model_adapter || "Not recorded");
    setText("providerInfo", report.mode || "Provider not recorded");
    setText("limitations", (report.limitations || []).map(x => "• " + x).join("\n") || "No limitations recorded.");

    setBadge("beforeBadge",
      report.before?.passed ? "PASSED" : "FAILED",
      report.before?.passed ? "" : "fail");
    setBadge("afterBadge",
      report.after?.passed ? "PASSED" : "FAILED",
      report.after?.passed ? "" : "fail");
    const verified = report.verification_status === "VERIFIED_TESTS_PASS";
    setBadge("overallStatus", verified ? "TESTS PASS" : "CHECK RESULTS", verified ? "" : "fail");
    setText("notice", verified ? "Run complete · evidence report updated." : "Run complete · inspect output and report.");
  } catch (error) {
    setBadge("overallStatus", "ERROR", "fail");
    setText("notice", "Could not complete run: " + error.message);
  } finally {
    button.disabled = false;
    button.innerHTML = "▶ &nbsp; Run repair &amp; verify";
  }
}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


@app.get("/api/report/download")
def download_report():
    if not REPORT.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No verification report exists yet. Run the repair pipeline first.")
    from fastapi.responses import FileResponse
    return FileResponse(
        path=REPORT,
        media_type="application/json",
        filename="verification_report.json",
    )


def _safe_project_file(relative_path: str) -> Path:
    """Resolve a user-selected .py file, confined to sample_project."""
    if not relative_path or not relative_path.lower().endswith(".py"):
        raise HTTPException(status_code=400, detail="Choose a Python (.py) file.")
    candidate = (PROJECT_DIR / relative_path).resolve()
    project_root = PROJECT_DIR.resolve()
    try:
        candidate.relative_to(project_root)
    except ValueError:
        raise HTTPException(status_code=400, detail="File must be inside sample_project.")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Selected Python file was not found.")
    if candidate.name.startswith("test_") or candidate.name.endswith("_test.py"):
        raise HTTPException(status_code=400, detail="Choose a source file, not a test file.")
    return candidate


def _run_project_tests():
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(PROJECT_DIR)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=90,
        )
        output = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        return {"passed": result.returncode == 0, "return_code": result.returncode,
                "output": output or ("pytest exited with code " + str(result.returncode))}
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") + "\n" + (exc.stderr or "")).strip()
        return {"passed": False, "return_code": -1,
                "output": (output + "\n" if output else "") + "pytest timed out after 90 seconds."}


@app.get("/api/files")
def list_project_files():
    if not PROJECT_DIR.exists():
        return {"files": []}
    files = []
    for path in PROJECT_DIR.rglob("*.py"):
        if path.name.startswith("test_") or path.name.endswith("_test.py"):
            continue
        if any(part in {".venv", "__pycache__", ".pytest_cache", ".proofstack_backups"} for part in path.parts):
            continue
        try:
            relative = path.resolve().relative_to(PROJECT_DIR.resolve())
            files.append(relative.as_posix())
        except ValueError:
            continue
    return {"files": sorted(files)}


@app.post("/api/run-custom")
def run_custom_repair(payload: dict):
    target = _safe_project_file(str(payload.get("target_file", "")))
    task = str(payload.get("task", "")).strip()
    if not task:
        raise HTTPException(status_code=400, detail="Enter a repair instruction.")
    if len(task) > 4000:
        raise HTTPException(status_code=400, detail="Repair instructions must be 4,000 characters or fewer.")

    try:
        original_source = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise HTTPException(status_code=400, detail=f"Could not read selected file: {exc}")

    before = _run_project_tests()
    try:
        # Keep the existing adapter and its configured NVIDIA Nemotron inference.
        from model_adapter import repair_code
        repaired_source = repair_code(
            original_source,
            task + "\n\nReturn a complete replacement for this single Python source file. "
                   "Preserve unrelated behavior. Do not include Markdown fences or explanations."
        )
        if not isinstance(repaired_source, str) or not repaired_source.strip():
            raise ValueError("The model returned empty or non-text code.")
        # Validate syntax before creating a backup or changing the target.
        compile(repaired_source, str(target), "exec")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model proposal rejected before file change: {exc}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    relative = target.resolve().relative_to(PROJECT_DIR.resolve())
    backup_path = BACKUP_DIR / timestamp / relative
    try:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_path)
        target.write_text(repaired_source, encoding="utf-8")
    except OSError as exc:
        # If writing failed after backup creation, attempt to restore original content.
        try:
            target.write_text(original_source, encoding="utf-8")
        except OSError:
            pass
        raise HTTPException(status_code=500, detail=f"Could not safely apply repair: {exc}")

    after = _run_project_tests()
    model_name = os.getenv("NVIDIA_MODEL") or os.getenv("MODEL") or "configured NVIDIA model"
    status = "VERIFIED_TESTS_PASS" if after["passed"] else "FAILED_TESTS"
    report = {
        "project": "ProofStack",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "real NVIDIA API inference",
        "model_adapter": "nvidia-openai-compatible",
        "model": model_name,
        "task": task,
        "target_file": relative.as_posix(),
        "backup": str(backup_path.relative_to(ROOT).as_posix()),
        "before": before,
        "after": after,
        "verification_status": status,
        "limitations": [
            "Pytest passing is evidence for the available tests, not proof of complete correctness.",
            "A backup was created before modifying the target file.",
            "This custom repair run uses NVIDIA API inference, not Nebius inference.",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return {
        "ok": after["passed"],
        "original_source": original_source,
        "repaired_source": repaired_source,
        "report": report,
    }


@app.post("/api/run")
def run_demo():
    # Capture the known baseline and then read the actual file written by app.py.
    original_source = BASELINE_SOURCE
    if REPORT.exists():
        REPORT.unlink()

    result = subprocess.run(
        [sys.executable, str(ROOT / "app.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )

    report = None
    if REPORT.exists():
        try:
            report = json.loads(REPORT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            report = None

    if report is None:
        return {
            "ok": False,
            "return_code": result.returncode,
            "detail": (
                (result.stdout or "") + "\n" + (result.stderr or "")
            ).strip() or "The repair run did not produce a readable report.",
        }

    try:
        repaired_source = CALCULATOR.read_text(encoding="utf-8")
    except OSError:
        repaired_source = ""

    return {
        "ok": result.returncode == 0,
        "return_code": result.returncode,
        "console_output": (
            (result.stdout or "") + "\n" + (result.stderr or "")
        ).strip(),
        "original_source": original_source,
        "repaired_source": repaired_source,
        "report": report,
    }
