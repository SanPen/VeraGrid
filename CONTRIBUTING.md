# Contributing

Thank you for contributing to **VeraGrid**.

## Before you start

- Open or find a GitHub issue for the bug, enhancement, or design discussion.
- For non-trivial changes, discuss the proposal with the maintainers before opening a pull request.
- Read [README.md](README.md), [BUILD.md](BUILD.md), [TESTING.md](TESTING.md), and [SECURITY.md](SECURITY.md) before submitting changes.

## Contribution process

All code contributions are submitted through pull requests.

- Base branch: `devel` for normal development work.
- Source branch: a feature branch in your fork is preferred.
- Small fixes should still start from an issue so the change has context and a review trail.

We review contributions for correctness, maintainability, compatibility with the VeraGrid data model, and user impact. Maintainers may request design changes before merge.

## What we accept

We accept:

- Bug fixes
- New simulation or file-format features
- Performance improvements
- Documentation improvements tied to code or user workflows
- Tests that improve regression coverage

We do not accept drive-by pull requests that only reformat code or perform unrelated style churn.

## Requirements for acceptable contributions

Every accepted contribution must:

- Be linked to a clear problem statement, issue, or design discussion.
- Keep changes scoped to a coherent purpose.
- Include or update automated tests for new behavior, bug fixes, or regressions.
- Update user or developer documentation when behavior, interfaces, or workflows change.
- Preserve compatibility unless the pull request clearly documents a breaking change.
- Avoid bundling unrelated refactors with behavioral changes.

## Coding standards

Use these rules unless maintainers instruct otherwise:

- Follow the existing style and structure of the touched module.
- Prefer clear, explicit code over clever shortcuts.
- Keep APIs, file-format handling, and solver behavior backwards compatible when practical.
- Add short comments only where they clarify non-obvious logic.
- Keep imports, dependencies, and generated artifacts under control.
- Do not introduce secrets, private credentials, or proprietary assets into the repository.

## Testing policy

VeraGrid requires automated tests for major new functionality and for bug fixes that can be reproduced.

- Add or update `pytest` tests under `src/tests`.
- Use filenames matching `test_*.py` so the suite picks them up through [pytest.ini](pytest.ini).
- Run the relevant tests locally before opening a pull request.
- If a change is difficult to test automatically, explain why in the pull request and provide the strongest practical regression coverage.

The expectation is simple: if behavior changes, the test suite should show it.

## How to run checks

Run the main automated test suite:

```bash
python -m pytest
```

Run a smaller target while developing:

```bash
python -m pytest src/tests
```

Run the linter used in CI:

```bash
python -m pylint $(git ls-files '*.py')
```

See [TESTING.md](TESTING.md) for more detail on tests, linting, and fuzzing.

## Pull request expectations

Pull requests should include:

- A concise summary of the problem and the fix
- References to related issues
- Notes about tests that were added or updated
- Documentation updates when external behavior changes
- Security impact when the change affects parsing, networking, authentication, serialization, or dependency updates

## Release and security notes

If your change fixes a user-visible security issue, mention it clearly in the pull request so it can be called out in the next release notes.

See [RELEASE.md](RELEASE.md) for the release-note policy.
