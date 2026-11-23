"""FFmpeg regression checks using synthetic media; no external services."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import edit
import media
import quality


class ExportChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.source = cls.root / 'source.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-f', 'lavfi',
                        '-i', 'testsrc2=size=480x270:rate=30:duration=2', '-f', 'lavfi',
                        '-i', 'sine=frequency=600:sample_rate=48000:duration=2',
                        '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac',
                        '-shortest', str(cls.source)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_ranges_only_plan_and_actual_export(self):
        (self.root / 'transcript.json').write_text(json.dumps({'segments': []}))
        plan = {'source': 'source.mp4', 'transcript': 'transcript.json', 'output': 'result.mp4',
                'ranges': [[0.1, 0.7], [1, 1.6]], 'disclosure': 'Synthetic test',
                'call_to_action': None, 'layout': {'face_crop': [0, 0, 160, 90],
                                                   'game_crop': [160, 0, 200, 250]}}
        file = self.root / 'plan.json'
        file.write_text(json.dumps(plan))
        with patch.object(edit, 'ROOT', self.root), contextlib.redirect_stdout(io.StringIO()):
            edit.run(file)
        report = json.loads((self.root / 'result.quality.json').read_text())
        self.assertTrue(report['technical_pass'])
        self.assertEqual(report['dimensions'], [1080, 1920])
        self.assertAlmostEqual(report['duration_seconds'], 1.2, delta=0.1)

    def test_silent_source_is_rejected(self):
        silent = self.root / 'silent.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(self.source),
                        '-af', 'volume=0', '-c:v', 'copy', str(silent)], check=True)
        with self.assertRaisesRegex(ValueError, 'audio audible'):
            media.render(silent, 0, 1, [], None, 'Test', self.root / 'forbidden.mp4')
        self.assertFalse((self.root / 'forbidden.mp4').exists())

    def test_landscape_source_keeps_full_width_and_audible_audio(self):
        output = self.root / 'landscape.mp4'
        media.render(self.source, 0, 1, [], None, 'Synthetic test', output, hook='TEST')
        report = quality.require_export(output)
        self.assertEqual(report['dimensions'], [1080, 1920])
        self.assertTrue(report['technical_pass'])
        frame = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(output),
                                        '-frames:v', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
        self.assertEqual(len(frame), 1080*1920*3)

    def test_missing_audio_is_rejected(self):
        video = self.root / 'no-audio.mp4'
        subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', str(self.source),
                        '-an', '-c:v', 'copy', str(video)], check=True)
        with self.assertRaisesRegex(ValueError, 'Falta vídeo o audio'):
            quality.inspect_export(video)

    def test_cut_does_not_show_words_from_removed_speech(self):
        transcript = [{'start': 0, 'end': 8, 'text': 'or so But if you have Lucia', 'words': [
            {'start':i, 'end':i+0.8, 'word':word}
            for i,word in enumerate('or so But if you have Lucia'.split())]}]
        groups = media.captions(transcript, start=2, end=7)
        self.assertEqual(' '.join(item[2] for item in groups), 'But if you have Lucia')
        self.assertEqual(media.caption_at(groups, 2.1), 'But if you')


if __name__ == '__main__':
    unittest.main(verbosity=2)
