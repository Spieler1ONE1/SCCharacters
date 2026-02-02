# Contributing to SCCharacters

First off, thanks for taking the time to contribute! 🎉

The following is a set of guidelines for contributing to SCCharacters and its packages. These are mostly guidelines, not rules. Use your best judgment and feel free to propose changes to this document in a pull request.

## Technology Stack

This project is built using:
- **Python 3.10+**: Core logic and backend.
- **PySide6 (Qt for Python)**: Modern, responsive GUI framework.
- **Star Citizen File Parsing**: Custom handlers for `.chf` and `.xml` configuration files.

We welcome contributions from developers of all skill levels interested in **game tools development**, **GUI programming**, or **Star Citizen community projects**.

## Code of Conduct

This project and everyone participating in it is governed by the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### ❓ Got a Question?

If you have questions about the codebase or how to get started, feel free to ask in our [Discord Server](https://discord.gg/TGjCmzHR).

### Reporting Bugs

This section guides you through submitting a bug report for SCCharacters. Following these guidelines helps maintainers and the community understand your report, reproduce the behavior, and find related reports.

- **Use a clear and descriptive title** for the issue to identify the problem.
- **Describe the exact steps which reproduce the problem** in as much detail as possible.
- **Provide specific examples to demonstrate the steps**. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples.
- **Describe the behavior you observed after following the steps** and point out what exactly is the problem with that behavior.
- **Explain which behavior you expected to see instead and why.**
- **Include screenshots and animated GIFs** which show you following the described steps and clearly demonstrate the problem.

### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for SCCharacters, including completely new features and minor improvements to existing functionality.

- **Use a clear and descriptive title** for the issue to identify the suggestion.
- **Provide a step-by-step description of the suggested enhancement** in as much detail as possible.
- **Provide specific examples to demonstrate the steps**.
- **Describe the current behavior** and **explain which behavior you expected to see instead** and why.

### Pull Requests

1.  Fork the repo and create your branch from `main`.
2.  If you've added code that should be tested, add tests.
3.  If you've changed APIs, update the documentation.
4.  Ensure the test suite passes.
5.  Make sure your code lints.
6.  Issue that pull request!

## Styleguides

### Git Commit Messages

*   Use the present tense ("Add feature" not "Added feature")
*   Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
*   Limit the first line to 72 characters or less
*   Reference issues and pull requests liberally after the first line

### Python Styleguide

All Python code is linted with `flake8` and formatted with `black`.

## Development Setup

1.  Clone the repository.
2.  Install dependencies: `pip install -r requirements.txt`.
3.  Run the application: `python src/main.py`.
