# Approval state machines

Upload, hero result, deletion, figure edit, palette application, poster structure, scientific-color unlock, and final release share one digest-bound gate:

```text
no proposal → proposed → approved
                    ↘ rejected
approved → revoked
proposal changed → proposed with a new digest
```

The v0.2 design sequence is:

```text
local_ready → brief_ready
→ awaiting_hero_approval
→ awaiting_deletion_approval
→ awaiting_figure_approval
→ awaiting_palette_approval
→ awaiting_structure_approval
→ ready_to_render → rendered → preflight_passed
```

Cloud upload is a capability gate immediately before provider transmission. Interfaces may navigate backward, but an upstream change invalidates relevant downstream approvals and artifacts. Locks remain in force until explicitly removed by the user.
