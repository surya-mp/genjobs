# Publishing to PyPI

This repository contains two independently versioned distributions:

- `genjobs-core`
- `genjobs-local`

They must be released separately. Do not publish an umbrella package that pulls
all integrations into one install.

## One-time repository setup

1. Create the public GitHub repository at `https://github.com/surya-mp/genjobs`.
2. Confirm the distribution names are available on [PyPI](https://pypi.org/).
   If either is unavailable, change its `project.name`, its documentation, and
   release tag convention before any release.
3. Create or sign into the PyPI maintainer account. Enable two-factor
   authentication.
4. On PyPI, configure a pending or trusted publisher for each distribution:
   owner `surya-mp`, repository `genjobs`, workflow
   `.github/workflows/publish.yml`, environment `pypi`. PyPI’s trusted-publisher
   guidance is the source of truth for the required fields.
5. In GitHub, create an environment named `pypi`. Require reviewer approval if
   releases should be manually approved. The workflow uses short-lived OpenID
   Connect credentials and does not require storing a PyPI token as a GitHub
   secret.

## Release checklist

1. Confirm `main` is green in GitHub Actions.
2. Add release notes to `CHANGELOG.md` under the package version being released.
3. Update the relevant package’s `version` in
   `packages/<distribution>/pyproject.toml`. Packages are versioned independently.
4. Build and inspect locally:

   ```bash
   python -m pip install --upgrade build twine
   python -m build packages/genjobs-core
   python -m build packages/genjobs-local
   twine check packages/genjobs-core/dist/* packages/genjobs-local/dist/*
   ```

5. Tag the commit with the exact package/version format:

   ```bash
   git tag genjobs-core-v0.1.0
   git push origin genjobs-core-v0.1.0
   ```

   The tag is the only publishing trigger. The workflow rejects a version that
   does not match package metadata, preventing accidental duplicate releases.
6. Approve the `pypi` GitHub environment if required, then verify the release on
   PyPI and install it into a clean virtual environment.
7. Create a GitHub release from the same tag, linking the relevant changelog
   section.

## Post-publish smoke test

```bash
python -m venv /tmp/genjobs-smoke
source /tmp/genjobs-smoke/bin/activate
python -m pip install genjobs-local
python -c "from genjobs_core import GenJobs; from genjobs_local import LocalArtifactStore"
```

## Security and artifacts

Never upload generated `dist/` contents by hand if trusted publishing is
configured. Never commit PyPI API tokens, `.pypirc`, cloud credentials, or test
artifacts. PyPI Trusted Publishing with the configured GitHub environment is the
supported release path.
