# Outreach Protocol (Governance v1.0)

## Objective: Build high-trust, low-volume, high-relevance connections.

## The "Human-in-the-Loop" Gate
1. **Scout Phase:** Agent identifies potential lead based on ICP.
2. **Analysis Phase:** Agent writes a "Relevance Summary" (Why this lead? What is the specific trigger event?).
3. **Draft Phase:** Agent drafts a personalized message using templates in `knowledge/templates/`.
4. **Approval Phase:** Agent deposits the draft in `workspace/outreach/drafts/`. 
   - **CRITICAL:** Agent is BANNED from sending messages. It can only "propose" messages to the Architect (Dharmendra).

## Communication Constraints
- **Zero Spam:** No bulk messaging. Every message must reference a specific post or company milestone.
- **Tone:** Professional, senior architect.
- **Data Compliance:** Never ingest or store personal health information (PHI) or sensitive internal client data.
- **Frequency:** Max 5 outreaches per day per platform.

## Reporting
- Every outreach attempt must be logged in `workspace/outreach/history/log.csv`.

## Related Files
- ICP and segment targets: `target_profile.md`