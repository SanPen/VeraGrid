# Conditional diagnostic

## Purpose

Preserves a source-model diagnostic as typed declarative data without producing an import-time logging side effect. This keeps the original condition, message and initialization scope available to solver or user-interface policies.

## Fields

- **Condition**: symbolic condition that activates the diagnostic.
- **Message**: exact source diagnostic text.
- **Initialization only**: whether the source evaluates the diagnostic only during initialization.

## Runtime behavior

The entry does not execute presentation or logging code. It retains the condition and message so an explicit runtime consumer can evaluate and present the diagnostic according to its own policy.
