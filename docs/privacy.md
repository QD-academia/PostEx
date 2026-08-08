# Privacy and upload approval

PostEx is local-first. Reading a local file authorizes local processing only; it does not authorize cloud processing.

Before transmission, PostEx redacts default exclusions and shows:

- provider and non-sensitive document label;
- included fields;
- excluded fields;
- estimated character count;
- canonical content digest.

Approval is bound to that disclosure digest. Provider, field, or content changes create a new proposal. Revocation blocks later calls. Provider adapters receive `ApprovedCloudPayload`, never a local source path.

For `local-only`, PostEx records that cloud summarization was unavailable and does not create a fake approval. Local parsing, image extraction, palette extraction, template checks, geometry checks, and preflight can continue.

Logs must omit manuscript bodies, prompts, raw evidence excerpts, API keys, author emails, embedded metadata, and unpublished filenames by default.

