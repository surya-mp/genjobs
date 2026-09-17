# Maintenance and operations

## Repository settings

Configure these settings in GitHub for `surya-mp/genjobs`:

- Protect `main`: require pull requests, passing CI, and resolved review
  conversations; disable force-pushes and branch deletion.
- Keep the `pypi` environment and require a reviewer for releases.
- Restrict who can modify workflows and who has write/admin access.

These are account-side controls and cannot be safely represented only in source
code. The workflows pin third-party actions to immutable commits and request
only the permissions required for each job.

## Release controls

Releases are tag-only. A tag must match the package metadata exactly, for
example `genjobs-core-v0.1.1`. CI validates source format, linting, strict types,
tests, distributions, package metadata, dependency vulnerabilities, and an SBOM
before code merges. Publishing uses PyPI OIDC Trusted Publishing, not a stored
long-lived token.

## Operational extensions

The core provides exponential retry configuration, retry timestamps, lifecycle
events, cooperative cancellation, and task heartbeats. Distributed backends
must add atomic job claiming and leases. Those mechanisms require a real durable
store/queue transaction boundary and must not be faked by a generic cloud SDK
wrapper.
