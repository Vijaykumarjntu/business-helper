# Business Helper: meeting scope change tracker

This project is a lightweight Python workflow for comparing long client meeting transcripts and identifying:

- what changed from the original agreed scope
- what is new
- what sits outside the agreed scope and should be quoted extra
- where a human approval gate prevents client-facing release

## Workflow

1. Add three meeting transcripts under `transcripts/`.
2. Review the generated summary.
3. Only release the client-facing brief after a human approves it.

## Run

From the project root:

```bash
python main.py --transcripts transcripts/meeting_01_kickoff.txt transcripts/meeting_02_follow_up.txt transcripts/meeting_03_final_review.txt
```

To allow the client-ready summary to be generated:

```bash
python main.py --approve --transcripts transcripts/meeting_01_kickoff.txt transcripts/meeting_02_follow_up.txt transcripts/meeting_03_final_review.txt
```

If approval is not given, the tool writes a review-only summary and stops before releasing anything client facing.
