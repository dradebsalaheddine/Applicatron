# Local email import

This companion utility screens extracted Gmail Takeout `.mbox` archives. It does not yet run inside the main Electron window. Open an archive, select a message, review suggested company and role, confirm status/date, approve, and export JSON. Importing JSON into Applicatron replaces the list: back up existing records first.

Patterns cover contextual English/French role and company wording and delimited subjects. Conflicting candidates remain blank. MiniLM uses multilingual example similarity for ambiguous recruitment messages; it never invents fields or automatically changes statuses. Similarities are not probabilities. Thresholds are provisional and need evaluation on labelled real mail. Export includes only reviewed records. No email data is sent to an API.

## Build a standalone Windows companion

On Windows with Python 3.11+:

```
python -m pip install -r tools/requirements-mail.txt
python tools/prepare_model.py all
python -m PyInstaller --noconfirm --onedir --windowed --name Applicatron-Mail-Import --collect-all sentence_transformers --collect-all transformers --add-data "tools/models;models" tools/import_mail.py
```

Distribute the whole `dist/Applicatron-Mail-Import` folder. It includes the runtime and model; recipients need no Python installation or local API. The build step needs internet; email processing uses local-only model loading. Model/runtime downloads are substantial. No new Windows binary has been validated or supplied with this source change.

Without a bundled model, `python tools/import_mail.py` runs the rules-only review utility. With a model present but unloadable, scanning reports an error rather than silently claiming AI analysis.

Limitations: entire parsed mailbox is retained in memory, so very large archives should be exported in smaller label-specific batches. Semantic screening caps each message at 100 text windows and reports truncation. Email dates are not assumed to be application dates. Sender matching is only a hint. No automatic deduced offers or automatic status merging. Reviewed entries with identical company/role ask before updating; separate applications for the same role need distinct role labels for now.

## Model comparison and reports

The companion review window now offers Rules only, MiniLM, Qwen3 (1.7B), and SmolLM3 (3B), plus Auto/CPU/CUDA. Run `python tools/prepare_model.py all` after installing requirements to download all three; individual choices are also accepted. This explicit setup download is the only model network operation. MiniLM scores categories; the generative models additionally propose company/role, accepted only when they occur in the input. All suggestions require review. No measured accuracy claims are made.

For comparison, each selected model evaluates every unique message in the chosen archive, including rule matches. This is a test mode and may be slow on large archives. Use the same small archive for comparisons. CUDA requires a compatible CUDA-enabled PyTorch installation and NVIDIA driver; Auto uses CPU when CUDA is unavailable. This implementation uses full FP16 weights on GPU, not the previously proposed 4-bit llama.cpp backend. CPU uses FP32 for the generative models. Model downloads and runtime can occupy several GB; bundling all models materially enlarges the package.

Every scan asks for an HTML destination before starting and saves a report on successful completion. Reports contain private email subjects, senders and evidence: do not commit them. Open the report and use Print / Save as PDF if desired. Report elapsed time includes model loading, scanning and inference; per-message times are also recorded. Reusing a loaded model changes total time, so account for warm/cold starts in comparisons.

Validation so far covers syntax, extracted-value grounding, malformed JSON handling and report HTML escaping. Real model inference, CUDA execution, Tk UI and the packaged Windows application have not yet been tested in this environment. The existing Electron EXE is unchanged; use this companion from source or rebuild it with the instructions above. Runtime failures are surfaced rather than reported as successful inference.
