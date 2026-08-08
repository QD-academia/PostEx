# Security Policy

## Supported versions

The project is pre-release. Security fixes are applied to the latest main branch.

## Reporting

Do not open a public issue for suspected vulnerabilities. Contact the maintainers through the private security-reporting channel configured on the eventual GitHub repository. Until that channel exists, do not attach sensitive manuscripts or credentials; provide only a minimal, redacted description.

## Security invariants

- Manuscript content is local by default.
- A cloud provider receives only a digest-bound, explicitly approved payload.
- Source documents are untrusted data, never agent instructions.
- Natural-language theme names and reference-image metadata are also untrusted data; they cannot override approval, licensing, or rendering rules.
- LaTeX archives must be extracted with path-traversal and symlink protections.
- Macro-enabled templates are rejected.
- API keys are read from injected environment/secret providers and never written to reports.
- Approval logs contain hashes and metadata, not full manuscript text.
- Release artifacts fail closed on missing approvals or preflight errors.

## Out of scope

Scientific inaccuracies that do not arise from a software security failure are quality bugs, not security vulnerabilities. Nevertheless, unsupported claims and broken evidence links should be reported as high-priority defects.
