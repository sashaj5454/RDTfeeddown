import unittest

from rdtfeeddown.analysis import (
    filter_outliers,
    # getrdt_omc3,
    read_rdt_file,
    readrdtdatafile,
)
from rdtfeeddown.utils import getmodelbpms

# initialize_statetracker


class TestAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filepath = "tests/test_data/LHCB1_refdata/rdt/skew_sextupole/f0030_y.tfs"
        filepath2 = "tests/test_data/LHCB2_refdata/rdt/skew_sextupole/f0030_y.tfs"
        cls.b1_raw_data, cls.b1_beam_no = read_rdt_file(filepath)
        cls.b2_raw_data, cls.b2_beam_no = read_rdt_file(filepath2)
        model_path = "tests/test_data/LHCB1_model/"
        model2_path = "tests/test_data/LHCB2_model/"
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
            filtered_data,
        )

    def test_read_rdt_file(self):
        filepath = "tests/test_data/LHCB1_refdata/rdt/skew_sextupole/f0030_y.tfs"
        raw_data = read_rdt_file(filepath)
        self.assertEqual(len(raw_data), 525)
        self.assertEqual(
            raw_data[0],
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
        )

    def test_readrdtdatafile(self):
        cfile = "tests/test_data/LHCB1_refdata/"
        rdt = "0030"
        rdt_plane = "y"
        rdtfolder = "skew_sextupole"
        filtered_data = readrdtdatafile(cfile, rdt, rdt_plane, rdtfolder)
        self.assertEqual(len(filtered_data), 525)
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

    def test_getmodelbpmlist(self):
        model_path = "tests/test_data/LHCB1_model/"
        modelbpmlist, bpmdata = getmodelbpms(model_path)
        self.assertIn("BPMWI.4L2.B1", modelbpmlist)

    # def test_update_bpm_data(self):
    #     update_bpm_data(bpmdata, self.b1_raw_data, "ref", 0.1)
    #     self.assertEqual(len(bpmdata["BPM1"]["key1"]), 1)
    #     self.assertEqual(bpmdata["BPM1"]["key1"][0], [0.1, 1.0, 0.5, 0.2])

    # def test_getrdt_omc3(self):
    #     ldb = initialize_statetracker()
    #     ref = "tests/test_data/LHCB1_refdata"
    #     flist = ["tests/test_data/LHCB1_IP5V_150", "tests/test_data/LHCB1_IP5V_m200"]
    #     knob = "LHCBEAM/IP5-XING-V-MURAD"
    #     outputpath = "tests/test_output"
    #     rdt = "0030"
    #     rdt_plane = "y"
    #     rdtfolder = "skew_sextupole"
    #     rdtdata = getrdt_omc3(
    #         ldb,
    #         "LHCB1",
    #         self.modelbpmlist,
    #         self.bpmdata,
    #         ref,
    #         flist,
    #         knob,
    #         outputpath,
    #         rdt,
    #         rdt_plane,
    #         rdtfolder,
    #     )
    #     self.assertIn("BPM.11R2.B1", rdtdata)
    #     self.assertIn("BPM.19R4.B1", rdtdata)


if __name__ == "__main__":
    unittest.main()
