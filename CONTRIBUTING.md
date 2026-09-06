# Contributing to VeritasAI

First off, thank you for considering contributing to VeritasAI! It's people like you that make VeritasAI such a great tool for fighting misinformation.

## How Can I Contribute?

### Reporting Bugs
This section guides you through submitting a bug report for VeritasAI. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.
* Use a clear and descriptive title for the issue to identify the problem.
* Describe the exact steps which reproduce the problem in as many details as possible.

### Suggesting Enhancements
This section guides you through submitting an enhancement suggestion for VeritasAI, including completely new features and minor improvements to existing functionality.
* Use a clear and descriptive title for the issue to identify the suggestion.
* Provide a step-by-step description of the suggested enhancement in as many details as possible.

### Pull Requests
* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible.
* End all files with a newline

## Local Development Setup

### Backend (Python/FastAPI)
1. Navigate to the `backend` directory.
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment.
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in the required keys.
6. Run the test suite: `pytest`
7. Start the server: `uvicorn main:app --reload`

### Frontend (React/Vite)
1. Navigate to the `src` directory.
2. Install dependencies: `npm install`
3. Start the dev server: `npm run dev`

### Code Style
* We use standard Python style (`PEP 8`). Please ensure your code follows this.
* For the frontend, we use ESLint. Run `npm run lint` before committing.

## Testing
We expect all new features and bug fixes to be accompanied by tests. The CI pipeline will automatically run `pytest` on all PRs. If the tests fail, the PR will not be merged.

Thanks for your contributions!
