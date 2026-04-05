# ⚙️ Task: Implement GitHub Actions CI

## 🎯 Objective

Automate the testing and linting process by setting up a Continuous Integration (CI) pipeline using GitHub Actions. This ensures that every code change is validated before being merged, maintaining high code quality and catching regressions early.

---

# 🏗️ 1. Scope of the CI Pipeline

The CI pipeline must automatically run the full suite of checks and tests on a clean environment.

## 🔹 1.1 Triggers
The workflow should be triggered on:
* **Push** events to the `main` branch.
* **Pull Request** events targeting the `main` branch.

## 🔹 1.2 Environment Setup
For each run, the pipeline must:
* Check out the code.
* Set up a Python environment (e.g., Python 3.11).
* Install dependencies (`pip install -r requirements.txt`).

## 🔹 1.3 Validation Steps
The pipeline must execute the following steps sequentially. If any step fails, the workflow should fail.

1. **Linting**:
   * Run the configured linter (e.g., `flake8`, `black`, or `pylint` depending on project setup) to enforce code style.
2. **Unit & Integration Tests**:
   * Run the standard `pytest` suite (`pytest app/tests/`).
3. **Acceptance Tests**:
   * Run the automated end-to-end (E2E) acceptance tests script created in Task 004 (`bash scripts/run_acceptance.sh` or `python scripts/test_acceptance.py`).
   * This ensures the application can install, start up, route traffic, generate alerts, and tear down successfully in a clean, ephemeral CI environment.

---

# 📁 2. Implementation Details

Create the GitHub Actions workflow file at:
`.github/workflows/ci.yml`

### Example Structure:
```yaml
name: CI Pipeline

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run Linting
        run: |
          # Add your linting command here, e.g. flake8 app/

      - name: Run Unit & Integration Tests
        run: |
          pytest app/tests/

      - name: Run E2E Acceptance Tests
        run: |
          # Add the command to run the acceptance test script
          # bash scripts/run_acceptance.sh
```

---

# 🧪 3. Acceptance Criteria

* [ ] `.github/workflows/ci.yml` file is created and correctly configured.
* [ ] The workflow is successfully triggered on PRs and pushes to `main`.
* [ ] The workflow correctly installs dependencies and runs the linter.
* [ ] The workflow successfully runs the `pytest` unit/integration test suite.
* [ ] The workflow successfully executes the E2E Acceptance tests.
* [ ] The pipeline fails if any of the tests or linting steps fail.

---

# ⏱️ 4. Estimated Time
* Workflow creation and configuration: 1 hour
* Debugging CI environment issues (e.g., getting acceptance tests to run cleanly in GitHub Actions): 1-2 hours

Total: **~2-3 hours**
