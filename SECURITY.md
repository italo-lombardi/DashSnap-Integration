# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | ✅        |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Report privately via GitHub: [Security Advisories](https://github.com/italo-lombardi/DashSnap-Integration/security/advisories/new)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 48 hours. If confirmed, a fix will be released as soon as possible and you will be credited in the changelog.

## Scope

This integration connects Home Assistant to the DashSnap recorder service. Key considerations:

- **DashSnap base URL**: The configured URL is stored in HA config entries. Ensure DashSnap is not exposed to untrusted networks.
- **No credentials stored**: This integration stores only the DashSnap base URL — no tokens or passwords. Credentials live in DashSnap's own config.
- **Service calls**: `dashsnap.record` and `dashsnap.record_ha` accept arbitrary URLs/paths. Restrict HA service call access to trusted users.
