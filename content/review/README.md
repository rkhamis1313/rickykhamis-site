Citation checklists live here.

`python gen/review.py --new` writes a dated checklist of the questions to test.
Ricky runs each one in ChatGPT and Perplexity, ticks whichever cited
rickykhamis.com, and saves. `python gen/review.py --apply <file>` turns those
ticks into queue order and appends the result to `review.log` in
`content/series.json`.

Filled-in checklists are kept as the audit trail for why the queue is ordered
the way it is.
