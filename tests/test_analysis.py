import unittest
from pathlib import Path

from rdtfeeddown.analysis import (
    filter_outliers,
    getrdt_omc3,
    read_rdt_file,
    readrdtdatafile,
)
from rdtfeeddown.data_handler import save_rdtdata
from rdtfeeddown.utils import getmodelbpms
from rdtfeeddown.validation_utils import validate_file_structure


class TestAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        test_dir = Path(__file__).resolve().parent
        filepath = test_dir / "test_data/LHCB1_refdata/rdt/skew_sextupole/f0030_y.tfs"
        filepath2 = test_dir / "test_data/LHCB2_refdata/rdt/skew_sextupole/f0030_y.tfs"
        cls.b1_raw_data, cls.b1_beam_no = read_rdt_file(filepath)
        cls.b2_raw_data, cls.b2_beam_no = read_rdt_file(filepath2)
        model_path = test_dir / "test_data/LHCB1_model/"
        model2_path = test_dir / "test_data/LHCB2_model/"
        cls.modelbpmlist, cls.bpmdata = getmodelbpms(model_path)
        cls.model2bpmlist, cls.bpmdata2 = getmodelbpms(model2_path)

    def test_filter_outliers(self):
        data = self.b1_raw_data[0:2]
        filtered_data = filter_outliers(data, threshold=3)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn(
            [
                "BPMWI.4L2.B1",
                73.3255,
                3,
                24.8030428977,
                6.34721879032,
                0.390472913362,
                0.214919748978,
                -19.1579666089,
                15.753198164,
            ],
            filtered_data[0],
        )

    def test_read_rdt_file(self):
        test_dir = Path(__file__).resolve().parent
        filepath = test_dir / "test_data/LHCB1_refdata/rdt/skew_sextupole/f0030_y.tfs"
        raw_data = read_rdt_file(filepath)
        self.assertEqual(len(raw_data[0]), 526)
        self.assertEqual(
            raw_data[0][1],
            [
                "BPMYB.4L2.B1",
                12.4345328059,
                -2.77953911438,
                12.1198914356,
                0.488253791687,
            ],
        )

    def test_readrdtdatafile(self):
        test_dir = Path(__file__).resolve().parent
        cfile = test_dir / "test_data/LHCB1_refdata/"
        rdt = "0030"
        rdt_plane = "y"
        rdtfolder = "skew_sextupole"
        filtered_data = readrdtdatafile(str(cfile), rdt, rdt_plane, rdtfolder)
        self.assertEqual(len(filtered_data[0]), 520)
        self.assertNotIn(
            [
                "BPMYB.5L2.B1",
                28.288,
                3,
                12.7882505699,
                5.11426097576,
                0.302609604707,
                0.3,
                -4.15066814928,
                12.0959210708,
            ],
            filtered_data,
        )

    def test_getmodel1bpmlist(self):
        test_dir = Path(__file__).resolve().parent
        model_path = test_dir / "test_data/LHCB1_model/"
        modelbpmlist, bpmdata = getmodelbpms(model_path)
        self.assertIn("BPMWI.4L2.B1", modelbpmlist)

    def test_getrdt_omc3_lhcb1(self):
        ldb = None
        ref = "tests/test_data/LHCB1_refdata"
        flist = ["tests/test_data/LHCB1_IP5V_150", "tests/test_data/LHCB1_IP5V_m150"]
        knob = ""
        rdt = "0030"
        rdt_plane = "y"
        rdtfolder = "skew_sextupole"
        b1_rdtdata = getrdt_omc3(
            ldb,
            "LHCB1",
            self.modelbpmlist,
            self.bpmdata,
            ref,
            flist,
            knob,
            rdt,
            rdt_plane,
            rdtfolder,
            sim=True,
            propfile="tests/test_data/b1_knobs.csv",
            log_func=print,
        )
        self.assertIn("BPM.11R2.B1", b1_rdtdata["data"])
        self.assertIn("BPM.19R4.B1", b1_rdtdata["data"])
        save_rdtdata(b1_rdtdata, "tests/test_output/LHCB1_rdtdata.json")

        required_metas = ["beam", "ref", "file_list", "rdt", "rdt_plane", "knob"]
        valid = validate_file_structure(b1_rdtdata, required_metas)
        self.assertTrue(valid, "File structure validation failed for LHCB1 RDT data")

    def test_getrdt_omc3_lhcb2(self):
        ldb = None
        ref = "tests/test_data/LHCB2_refdata"
        flist = ["tests/test_data/LHCB2_IP5V_200", "tests/test_data/LHCB2_IP5V_m200"]
        knob = ""
        rdt = "0030"
        rdt_plane = "y"
        rdtfolder = "skew_sextupole"
        b2_rdtdata = getrdt_omc3(
            ldb,
            "LHCB2",
            self.model2bpmlist,
            self.bpmdata2,
            ref,
            flist,
            knob,
            rdt,
            rdt_plane,
            rdtfolder,
            sim=True,
            propfile="tests/test_data/b2_knobs.csv",
            log_func=print,
        )
        self.assertIn("BPM.11R2.B2", b2_rdtdata["data"])
        self.assertIn("BPM.19R4.B2", b2_rdtdata["data"])

        save_rdtdata(b2_rdtdata, "tests/test_output/LHCB2_rdtdata.json")

        required_metas = ["beam", "ref", "file_list", "rdt", "rdt_plane", "knob"]
        valid = validate_file_structure(b2_rdtdata, required_metas)
        self.assertTrue(valid, "File structure validation failed for LHCB1 RDT data")


if __name__ == "__main__":
    unittest.main()
