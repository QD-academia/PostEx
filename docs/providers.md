# Provider adapters

`postex.providers.base.Provider` is the only interface visible to workflow code. The OpenAI and Anthropic adapters:

1. verify matching upload approval;
2. lazily import the optional SDK;
3. translate a neutral `ProviderRequest`;
4. normalize output into `ProviderResponse`.

Provider adapters cannot parse local files, select upload fields, apply deletions, choose palettes, or render slides. Credentials come from the SDK's standard environment or an injected client. Model names are configuration, not frozen defaults; deployments should choose an approved model and record it in the evidence audit.

Network calls are not exercised by unit tests. Contract tests should use injected fake clients and assert that unapproved requests never reach them.

