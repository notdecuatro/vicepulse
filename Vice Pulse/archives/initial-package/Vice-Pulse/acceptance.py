"""Offline acceptance checks for state transitions. No credentials or network."""
import contextlib
import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

import services
import vice

class Pipeline(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for name,value in (("ROOT",self.root),("STATE",self.root/"state"),("CONFIG",self.root/"campaign.json")):
            p=patch.object(vice,name,value); p.start(); self.addCleanup(p.stop)
        self.db=vice.db_file()
        self.addCleanup(self.db.close)
        self.day="2026-11-22"
        s=self.root/"source"; s.write_bytes(b"fixture only")
        (self.root/"evidence.txt").write_text("Synthetic fixture only, offline test.")
        self.c=json.loads((Path(__file__).parent/"campaign.example.json").read_text())
        self.c.update(logo_required=False,logo="",verified_on=self.day,accepting_clips=True,
                      remaining_budget=1,joined=True,preapproval_required=False,submission_session_ready=True)
        asset=self.c["sources"][0]
        asset.update(file="source",sha256=vice.digest(s),evidence_file="evidence.txt",platforms=list(services.NETWORKS))
        asset["rights"]=dict.fromkeys(asset["rights"],True)
        for n,p in self.c["platforms"].items():
            p.update(channel_id=n,authorized=True,native_disclosure_supported=True)
        self.api=Mock()
        self.api.upload.return_value="https://example.invalid/clip.mp4"
        self.api.send.side_effect=lambda p:"fake-"+p["channelId"]+str(self.api.send.call_count)
        self.analyze=lambda *a:{"segments":[],"choices":[{"start":i,"end":i+18,"title":str(i)} for i in (0,18)]}
        self.render=Mock(side_effect=lambda *a:a[-1].write_bytes(str(a[1]).encode()))

    def produce(self):
        vice.produce(self.db,self.c,self.day,self.analyze,self.render)

    def send(self,slot=1,draft=True):
        vice.dispatch(self.db,self.c,self.day,slot,draft,self.api)

    def test_two_clips_six_drafts_repeat_without_duplicates(self):
        self.produce(); self.produce()
        for slot in (1,2,1,2):
            self.send(slot)
        self.assertEqual(self.render.call_count,2)
        self.assertEqual(self.api.upload.call_count,2)
        self.assertEqual(self.api.send.call_count,6)
        self.assertEqual(self.db.execute("select count(*) from jobs where status='draft'").fetchone()[0],6)
        for call in self.api.send.call_args_list:
            v=call.args[0]; self.assertTrue(v["saveToDraft"])
            self.assertTrue(v["assets"][0]["video"]["url"].startswith("https://"))
            if v["channelId"]=="youtube": self.assertEqual(v["metadata"]["youtube"]["categoryId"],"20")

    def test_ambiguous_response_survives_restart(self):
        self.produce()
        self.api.send.side_effect=TimeoutError()
        with self.assertRaises(TimeoutError): self.send()
        self.api.send.side_effect=lambda p:"id-"+p["channelId"]
        self.send()
        self.assertEqual(self.api.send.call_count,3)
        self.assertEqual(self.db.execute("select count(*) from jobs where status='sending'").fetchone()[0],1)

    def test_live_receipts_are_distinct_from_rewards(self):
        self.produce(); self.send(draft=False)
        self.api.receipt.side_effect=lambda i:{"id":i,"status":"sent","sentAt":"2026-11-22T10:00:00Z","externalLink":"https://example.invalid/"+i}
        with contextlib.redirect_stdout(io.StringIO()) as log: vice.sync(self.db,self.api)
        self.assertEqual(log.getvalue().count("submit_before"),3)
        self.assertEqual(self.db.execute("select count(*) from jobs where reward_ref is not null").fetchone()[0],0)

    def test_rights_change_and_tampering(self):
        self.produce()
        self.c["sources"][0]["rights"]["audio"]=False
        with self.assertRaises(ValueError): self.send()
        self.c["sources"][0]["rights"]["audio"]=True
        (vice.STATE/(self.day+"-1.mp4")).write_bytes(b"changed")
        with self.assertRaises(ValueError): self.send()
        self.api.upload.assert_not_called()

    def test_expired_campaign_and_native_disclosure(self):
        vice.atomic_json(vice.CONFIG,self.c)
        with self.assertRaises(ValueError): vice.load_config("2026-11-23")
        self.produce()
        self.c["platforms"]["tiktok"]["native_disclosure_supported"]=False
        with self.assertRaises(ValueError): self.send(draft=False)
        self.api.upload.assert_not_called()

    def test_exhausted_source_is_not_reused(self):
        self.produce()
        with self.assertRaises(ValueError):
            vice.produce(self.db,self.c,"2026-11-23",self.analyze,self.render)
        self.assertEqual(self.render.call_count,2)

if __name__=="__main__":
    unittest.main(verbosity=2)

