"""Exercise download progress against the actual Hub 0.x progress adapter, without model weights."""
import importlib
import logging
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from model_download import download_model

class DownloadTests(unittest.TestCase):
    def run_download(self, root, fail=False, wrong_size=False):
        events=[]
        metadata=SimpleNamespace(sha='a'*40,siblings=[SimpleNamespace(rfilename='config.json',size=4),SimpleNamespace(rfilename='model.safetensors',size=1000),SimpleNamespace(rfilename='pytorch_model.bin',size=1000),SimpleNamespace(rfilename='onnx/model.onnx',size=1000)])
        progress=importlib.import_module('huggingface_hub.utils.tqdm')
        original=progress.tqdm
        def transfer(repo, filename, revision, local_dir):
            self.assertEqual(revision, 'a'*40)
            size=4 if filename=='config.json' else 1000
            with progress._get_progress_bar_context(desc=filename,log_level=logging.INFO,total=size,initial=size//2) as bar:
                bar.update(size-size//2)
            if fail:raise OSError('Connection lost')
            path=Path(local_dir)/filename
            path.write_bytes(b'x'*(size-1 if wrong_size else size))
            return str(path)
        with patch('huggingface_hub.HfApi') as api, patch('huggingface_hub.hf_hub_download',side_effect=transfer) as fetch:
            api.return_value.model_info.return_value=metadata
            try:download_model('example/repo',root,'MiniLM',lambda kind,**kw:events.append(dict(type=kind,**kw)))
            finally:self.assertIs(progress.tqdm,original)
            self.assertEqual(fetch.call_count,2)
        return events

    def test_progress_resume_and_ready(self):
        with tempfile.TemporaryDirectory() as root:
            events=self.run_download(root)
            self.assertEqual(events[-1]['type'],'done')
            self.assertEqual(events[-1]['downloadedBytes'],1004)
            updates=[e for e in events if e['type']=='download' and 'downloadedBytes' in e]
            self.assertTrue(any(0<e['downloadedBytes']<1004 for e in updates))
            self.assertTrue(all(e['downloadedBytes']<=1004 for e in updates))
            self.assertEqual((Path(root)/'.ready').read_text(),'a'*40)

    def test_failed_or_incomplete_transfer_never_marks_ready(self):
        for option in [{'fail':True},{'wrong_size':True}]:
            with self.subTest(option=option), tempfile.TemporaryDirectory() as root:
                with self.assertRaises((OSError,ValueError)):
                    self.run_download(root,**option)
                self.assertFalse((Path(root)/'.ready').exists())

if __name__=='__main__':unittest.main()
