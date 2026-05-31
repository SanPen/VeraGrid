## Summary

- What problem does this change solve?
- What behavior changes should reviewers focus on?

## Checklist

- [ ] The change is linked to an issue or design discussion
- [ ] I added or updated automated tests for the changed behavior
- [ ] I updated documentation for user-visible changes
- [ ] I called out any breaking change or migration impact
- [ ] I described any security impact if parsing, networking, serialization, or authentication changed

## Verification

- [ ] `python -m pytest`
- [ ] `python -m pylint $(git ls-files '*.py')`

If a check was skipped, explain why.

## Release notes

- [ ] No release-note entry needed
- [ ] Release notes required
- [ ] Security fix to mention in release notes
