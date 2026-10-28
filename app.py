
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from model_adapter import repair_code

load_dotenv()

ROOT = Path(__file__).resolve().parent
DEMO = ROOT / "sample_project"
SOURCE = DEMO / "calculator.py"
TESTS = DEMO / "test_calculator.py"
REPORT = ROOT / "verification_report.json"

BROKEN_SOURCE = '''def calculate_total(price: float, discount: float) -> float:
    """Calculate the final price after a fractional discount."""
    return price - discount
'''

TEST_SOURCE = '''from calculator import calculate_total


def test_no_discount():
    assert calculate_total(100, 0) == 100


def test_twenty_percent_discount():
    assert calculate_total(100, 0.2) == 80


def test_full_discount():
    assert calculate_total(100, 1) == 0
'''


def run_tests():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            str(TESTS),
        ],
        cwd=DEMO,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return {
        "exit_code": result.returncode,
        "output": (result.stdout + "\n" + result.stderr).strip(),
        "passed": result.returncode == 0,
    }


def main():
    DEMO.mkdir(exist_ok=True)

    # Reset the demonstration to a known broken starting point.
    SOURCE.write_text(BROKEN_SOURCE, encoding="utf-8")
    TESTS.write_text(TEST_SOURCE, encoding="utf-8")

    print("\nProofStack — Nemotron Repair Demo")
    print("=" * 42)

    print("\n1. Running tests before repair...")
    before = run_tests()
    print(before["output"] or "(No test output)")

    if before["passed"]:
        print("Unexpected result: the broken example passed.")
        sys.exit(1)

    print("\n2. Asking NVIDIA Nemotron to propose a fix...")
    original_source = SOURCE.read_text(encoding="utf-8")

    try:
        proposed_source = repair_code(
            original_source,
            "Fix the fractional discount calculation. "
            "The discount is a fraction between 0 and 1; "
            "the final price should be price * (1 - discount).",
        )
    except Exception as exc:
        print(f"Nemotron request failed: {type(exc).__name__}: {exc}")
        sys.exit(2)

    if not proposed_source.strip() or proposed_source == original_source:
        print("Nemotron did not produce a changed source file.")
        sys.exit(2)

    # Compile before replacing the file.
    try:
        compile(proposed_source, str(SOURCE), "exec")
    except SyntaxError as exc:
        print(f"Nemotron proposed invalid Python: {exc}")
        sys.exit(2)

    # Only replace the demo file after the proposed code parses.
    SOURCE.write_text(proposed_source, encoding="utf-8")
    print("Nemotron's proposed patch was applied.")

    print("\n3. Running tests after repair...")
    after = run_tests()
    print(after["output"] or "(No test output)")

    model_name = __import__("os").getenv(
        "NVIDIA_MODEL", "unknown"
    )

    report = {
        "project": "ProofStack",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_adapter": "nvidia-openai-compatible",
        "model": model_name,
        "mode": "real NVIDIA API inference",
        "task": "Fix fractional discount calculation",
        "before": before,
        "after": after,
        "verification_status": (
            "VERIFIED_TESTS_PASS" if after["passed"]
            else "FAILED"
        ),
        "limitations": [
            "The model proposes code; pytest determines the test result.",
            "Passing tests do not prove all behavior is correct.",
            "This run uses NVIDIA API inference, not Nebius inference.",
        ],
    }

    REPORT.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"\n4. Evidence report saved to: {REPORT.name}")
    print(f"Status: {report['verification_status']}")

    if not after["passed"]:
        print("Verification failed. Inspect the proposed patch and test output.")
        sys.exit(1)

    print("\nMilestone PASSED: Nemotron proposed a fix verified by pytest.")


if __name__ == "__main__":
    main()
