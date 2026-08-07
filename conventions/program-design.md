# Program Design Artifact

The layer between architecture ("which services talk to each other") and code ("here are the file changes") — produced before the detailed plan, so structural problems surface before implementation makes them expensive.

For tasks beyond simple oneshot changes, produce a **program design artifact** before writing the detailed plan. It captures the shape of the code so the reviewer can catch structural problems before 800 lines of implementation make them expensive to fix.

The program design artifact has three parts:

1. **Call-stack tree diff** — Show the control flow that will change, using `+` for new call frames and `-` for removed ones. This lets the reviewer see at a glance how the call graph is being restructured:
   ```
   handleRequest()
     → validateInput()
   + → resolvePermissions()    # new: moved out of middleware
     → executeQuery()
   -   → legacyTransform()     # removed: replaced by pipeline
   +   → pipeline.run()        # new: streaming pipeline
   +     → stage1.process()
   +     → stage2.process()
     → formatResponse()
   ```

2. **File-tree diff** — Show what files are being created, renamed, modified, or deleted. This keeps the reviewer in touch with the layout of the codebase:
   ```
   src/
   + api/permissions.ts          # new: extracted from middleware
   ~ api/handlers/query.ts       # modified: swap legacy for pipeline
   - api/transforms/legacy.ts    # deleted: replaced by pipeline stages
   + pipeline/
   +   runner.ts                 # new: streaming pipeline orchestrator
   +   stages/
   +     stage1.ts
   +     stage2.ts
   ```

3. **Key types and method signatures** — For the main new functions, write the types and signatures without the implementation. These are decisions you'd otherwise make implicitly during code review, at the most expensive possible moment to change your mind:
   ```typescript
   interface PipelineStage<TIn, TOut> {
     name: string;
     process(input: TIn, ctx: PipelineContext): Promise<TOut>;
   }

   function createPipeline(stages: PipelineStage[]): Pipeline;
   function resolvePermissions(userId: string, resource: Resource): Promise<PermissionSet>;
   ```

**When to include this step:**
- ~40% of tasks are small enough to skip this — oneshot with 1–2 rounds of feedback.
- Medium tasks: combine this with the architecture overview in one plan doc.
- Large tasks: this gets its own review before implementation begins.
- Pure refactors: skip the product/requirements step but still do program design.

Present the program design to the user for review before writing the detailed implementation plan. Disagreements about code shape cost minutes here and hours during code review.
