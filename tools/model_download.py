"""Pinned, cached model downloads with byte progress sent to the desktop UI."""
import fnmatch
import importlib
import os
import time
from pathlib import Path

IGNORE = ['*.gguf', '*.onnx', '*.h5', '*.msgpack', '*.bin', 'onnx/*', 'openvino/*']

def download_model(repo, folder, name, emit):
    # HTTP transfers expose byte callbacks; keep Xet from hiding progress in its native client.
    os.environ['HF_HUB_DISABLE_XET'] = '1'
    from huggingface_hub import HfApi, hf_hub_download
    # Hub 0.x (required by Transformers 4.x) lacks hf_hub_download(tqdm_class=...).
    # This worker is isolated and downloads serially: scope its progress implementation
    # to the transfer and restore it afterwards. Both Hub 0.x progress paths are covered.
    progress_module = importlib.import_module('huggingface_hub.utils.tqdm')
    download_module = importlib.import_module('huggingface_hub.file_download')
    tqdm = progress_module.tqdm
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    emit('download', model=name, stage='Checking model files', detail='Contacting Hugging Face; existing downloads will be reused.')
    info = HfApi().model_info(repo, files_metadata=True)
    files = [f for f in info.siblings if not any(fnmatch.fnmatch(f.rfilename, p) for p in IGNORE)]
    if not files:
        raise ValueError('No model files were found.')
    total = sum(f.size or 0 for f in files)
    known = all(f.size is not None for f in files)
    completed = 0
    transferred = 0
    started = time.monotonic()
    last_emit = 0
    current = {'name': '', 'bytes': 0, 'index': 0}

    def progress(force=False):
        nonlocal last_emit
        now = time.monotonic()
        if not force and now - last_emit < .2:
            return
        last_emit = now
        done = min(completed + current['bytes'], total) if known else completed + current['bytes']
        speed = transferred / max(now - started, .01)
        emit('download', model=name, stage='Downloading '+name, file=current['name'],
             completedFiles=current['index'], totalFiles=len(files), downloadedBytes=done,
             totalBytes=total if known else None, bytesPerSecond=round(speed),
             etaSeconds=round((total-done)/speed) if known and speed > 0 else None)

    class Progress(tqdm):
        def __init__(self, *args, **kwargs):
            kwargs['disable'] = False
            super().__init__(*args, **kwargs)
            current['bytes'] = self.n  # Includes a resumed partial transfer.
            progress(True)

        def display(self, *args, **kwargs):
            return None  # JSON-lines stdout is the sole UI channel.

        def update(self, n=1):
            nonlocal transferred
            result = super().update(n)
            transferred += n
            current['bytes'] = self.n
            progress()
            return result

    for index, item in enumerate(files):
        current.update(name=item.rfilename, bytes=0, index=index)
        progress(True)
        # Pin all files to one immutable revision. Hub validates cached files and reuses partials.
        previous_progress = progress_module.tqdm
        previous_download = download_module.tqdm
        try:
            progress_module.tqdm = download_module.tqdm = Progress
            downloaded = hf_hub_download(repo, item.rfilename, revision=info.sha,
                                         local_dir=folder)
        finally:
            progress_module.tqdm = previous_progress
            download_module.tqdm = previous_download
        size = Path(downloaded).stat().st_size
        if item.size is not None and size != item.size:
            raise ValueError('Downloaded file has an unexpected size: '+item.rfilename)
        completed += item.size if item.size is not None else size
        current.update(bytes=0, index=index+1)
        progress(True)
    (folder / '.ready').write_text(info.sha or 'ready', encoding='utf-8')
    emit('done', model=name, downloadedBytes=completed, totalBytes=total if known else None)
