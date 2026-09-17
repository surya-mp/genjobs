# Security policy

## Supported versions

Until a stable release, only the latest minor release of each package is
supported. Security fixes are released as soon as practical.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use the repository’s
private GitHub security advisory reporting flow, or contact the maintainers by
the security address published in the repository once it exists. Include a
reproduction, affected package/version, impact, and any suggested mitigation.

We will acknowledge reports within seven days, confirm scope before publishing
details, and credit reporters if they wish.

## Integration security

GenJobs is a library, not a security boundary. Backend authors must document
authentication, authorization, tenant isolation, queue-message integrity,
artifact access, encryption, retention, and cleanup. Never put cloud
credentials or model/API secrets in job payloads or artifact metadata.
