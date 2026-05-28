# Release Process

This document defines the minimum release expectations for VeraGrid packages and GitHub releases.

## Versioning

Each release intended for users must have a unique version identifier.

The project publishes versioned packages and versioned GitHub releases. Release tags should match the package version being published.

## Release artifacts

For each release, publish:

- A Git tag
- Package artifacts for the affected package
- Human-readable release notes in GitHub Releases

## Release notes policy

Release notes must summarize the major changes for users. They should not be a raw commit log.

Each release note should include, when relevant:

- New features
- Fixed bugs
- Breaking changes
- Upgrade notes or migration steps
- Documentation changes
- Security fixes

## Security fixes in release notes

If a release fixes a publicly known runtime vulnerability in VeraGrid itself, and that vulnerability already had a CVE or similar public identifier when the release was created, the release notes must identify it explicitly.

If a release contains no such VeraGrid vulnerability fixes, the release notes should say that there are no publicly disclosed product vulnerabilities fixed in that release.

This requirement applies to VeraGrid itself, not to third-party dependency advisories.

## Release checklist

Before release:

- Ensure the relevant tests pass
- Ensure linting and security workflows are green
- Verify version numbers and tags
- Review dependency changes
- Prepare release notes using the policy above

After release:

- Publish the GitHub Release
- Publish package artifacts
- Announce important breaking changes or security fixes in the release notes
