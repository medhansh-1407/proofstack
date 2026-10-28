# ProofStack

**An AI-powered Python debugging agent that repairs code and verifies fixes using automated tests.**

ProofStack uses NVIDIA Nemotron to propose Python code repairs, runs automated tests before and after changes, and displays the results in a web dashboard.

## Features

- AI-assisted Python bug fixing
- Automated test execution using pytest
- Before-and-after code comparison
- Verification reports with test results
- Custom repair instructions
- Python source file selection
- Timestamped backups before modifying source files

## Tech Stack

- Python
- FastAPI
- Uvicorn
- pytest
- NVIDIA Nemotron
- OpenAI-compatible API client

## Project Structure

```text
proofstack/
├── sample_project/
│   ├── calculator.py
│   └── test_calculator.py
├── app.py
├── model_adapter.py
├── web_app.py
├── test_nvidia_connection.py
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/proofstack.git
cd proofstack
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure your API credentials

Create a local `.env` file in the project root and add the NVIDIA API configuration required by `model_adapter.py`.

Keep your API key private. Never commit `.env` to GitHub.

### 5. Run the repair demonstration

```bash
python app.py
```

### 6. Launch the web dashboard

```bash
python -m uvicorn web_app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in your browser.

## Example Verification

In the sample calculator demonstration, the initial test run produces two failing tests and one passing test. After the AI-generated repair, all three tests pass.

ProofStack presents the test results and code changes so developers can inspect the outcome of a repair.

## Current Limitations

The current implementation uses NVIDIA API inference. Nebius Token Factory or Nebius AI Cloud integration has not yet been verified.

A passing test suite demonstrates that the configured tests pass; it does not guarantee that every possible bug has been eliminated.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
