# Contributing to codesphere-python

First off, thank you for considering contributing to our project! We welcome any contributions, from fixing bugs and improving documentation to submitting new features.

---

## How Can I Contribute?

* **Reporting Bugs**: If you find a bug, please open a **GitHub Issue** and provide as much detail as possible, including steps to reproduce it.
* **Suggesting Enhancements**: If you have an idea for a new feature or an improvement, open a **GitHub Issue** to discuss it. This lets us coordinate our efforts and prevent duplicated work.
* **Pull Requests**: If you're ready to contribute code, documentation, or tests, you can open a Pull Request.

---

## Development Setup

To get your local development environment set up, please follow these steps:

1.  **Fork the repository** on GitHub.
2.  **Clone your forked repository** to your local machine:
    ```bash
    git clone [https://github.com/YOUR_USERNAME/codesphere-python.git](https://github.com/YOUR_USERNAME/codesphere-python.git)
    cd codesphere-python
    ```
3.  **Set up the project and install dependencies.** We use `uv` for package management. The following command will create a virtual environment and install all necessary dependencies for development:
    ```bash
    make install
    ```
4.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

You are now ready to start developing!

---

## Contribution Workflow

1.  **Create a new branch** for your changes. Please use a descriptive branch name.
    ```bash
    # Example for a new feature:
    git checkout -b feature/my-new-feature

    # Example for a bug fix:
    git checkout -b fix/bug-description
    ```
2.  **Make your code changes.** Write clean, readable code and add comments where necessary.
3.  **Format and lint your code** before committing to ensure it meets our style guidelines.
    ```bash
    make format
    make lint
    ```
4.  **Run the tests** to ensure that your changes don't break existing functionality.
    ```bash
    make test
    ```
5.  **Commit your changes.** We follow the **[Conventional Commits](https://www.conventionalcommits.org/)** specification. You can use our commit command, which will guide you through the process:
    ```bash
    make commit
    ```
6.  **Push your changes** to your forked repository.
    ```bash
    git push origin feature/my-new-feature
    ```
7.  **Open a Pull Request** from your fork to our `main` branch. Please provide a clear title and description for your changes, linking to any relevant issues.

---

## Pull Request Guidelines

* Ensure all tests and CI checks are passing.
* If you've added new functionality, please add corresponding tests.
* Keep your PR focused on a single issue or feature.
* A maintainer will review your PR and provide feedback.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please be respectful and considerate in all your interactions.