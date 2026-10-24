# Local email import

This companion utility screens extracted Gmail Takeout `.mbox` archives. It does not yet run inside the main Electron window. Open an archive, select a message, review suggested company and role, confirm status/date, approve, and export JSON. Importing JSON into Applicatron replaces the list: back up existing records first.

Patterns cover contextual English/French role and company wording and delimited subjects. Conflicting candidates remain blank. MiniLM uses multilingual example similarity for ambiguous recruitment messages; it never invents fields or automatically changes statuses. Similarities are not probabilities. Thresholds are provisional and need evaluation on labelled real mail. Export includes only reviewed records. No email data is sent to an API.

## Build a standalone Windows companion

On Windows with Python 3.11+:

```
python -m pip install -r tools/requirements-mail.txt
python tools/prepare_model.py
python -m PyInstaller --noconfirm --onedir --windowed --name Applicatron-Mail-Import --collect-all sentence_transformers --collect-all transformers --add-data "tools/models;models" tools/import_mail.py
```

Distribute the whole `dist/Applicatron-Mail-Import` folder. It includes the runtime and model; recipients need no Python installation or local API. The build step needs internet; email processing uses local-only model loading. Model/runtime downloads are substantial. No new Windows binary has been validated or supplied with this source change.

Without a bundled model, `python tools/import_mail.py` runs the rules-only review utility. With a model present but unloadable, scanning reports an error rather than silently claiming AI analysis.

Limitations: entire parsed mailbox is retained in memory, so very large archives should be exported in smaller label-specific batches. Semantic screening caps each message at 100 text windows and reports truncation. Email dates are not assumed to be application dates. Sender matching is only a hint. No automatic deduced offers or automatic status merging. Reviewed entries with identical company/role ask before updating; separate applications for the same role need distinct role labels for now.
