# Publishing and maintenance

The package ecosystem publishes independently: `genjobs-core` and
`genjobs-local` are separate PyPI projects with their own versions. Cloud,
server, CLI, and model integration packages will follow the same rule.

Before a first release, maintainers must choose a canonical GitHub repository,
replace the repository URL placeholders in package metadata, confirm the PyPI
names are available, and configure a PyPI Trusted Publisher for each
distribution. The publisher must be restricted to this repository’s
`.github/workflows/publish.yml` workflow and `pypi` GitHub environment.

Releases are made from tags named `genjobs-core-vX.Y.Z` or
`genjobs-local-vX.Y.Z`. The workflow validates that the tag’s version matches
the relevant package metadata, builds the wheel and source distribution, and
uses OpenID Connect Trusted Publishing rather than a long-lived PyPI token.

The complete operational checklist, including local build commands, post-release
smoke testing, and security rules, is maintained in `PUBLISHING.md` at the root
of the source repository.
