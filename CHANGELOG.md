# Changelog

All notable changes follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-09-17

### Added

- Exponential retry policy with queue-delayed retry scheduling and retry timestamps.
- JSON-boundary payload validation and configurable payload-size limits.
- Lifecycle observers, worker heartbeats, and cooperative cancellation requests.
- Tag-only releases, pinned workflow actions, dependency auditing, SBOM generation,
  and release artifact attestations through PyPI Trusted Publishing.

## [0.1.0] - 2026-09-17

### Added

- Initial pre-release package baseline.
- Initial workspace with independently installable `genjobs-core` and
  `genjobs-local` packages.
- Portable job, task, queue, job-store, and artifact-store contracts.
- Local test/development backends and publication automation scaffold.
