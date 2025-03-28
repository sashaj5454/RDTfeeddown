import unittest
from rdtfeeddown.analysis import (
    filter_outliers,
    read_rdt_file,
    readrdtdatafile,
    update_bpm_data,
    getrdt_omc3
)

class TestAnalysis(unittest.TestCase):

    def test_filter_outliers(self):
        data = [
            ['BPM1', 1.0, 0.5, 0.2],
            ['BPM2', 2.0, 1.5, 1.2],
            ['BPM3', 100.0, 50.0, 20.0]  # outlier
        ]
        filtered_data = filter_outliers(data, threshold=3)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn(['BPM3', 100.0, 50.0, 20.0], filtered_data)

    def test_read_rdt_file(self):
        filepath = 'tests/test_data/test_rdt_file.tfs'
        raw_data = read_rdt_file(filepath)
        self.assertEqual(len(raw_data), 3)
        self.assertEqual(raw_data[0], ['BPM1', 1.0, 0.5, 0.2])

    def test_readrdtdatafile(self):
        cfile = 'tests/test_data'
        rdt = '0030'
        rdt_plane = 'x'
        rdtfolder = 'normal_quadrupole'
        filtered_data = readrdtdatafile(cfile, rdt, rdt_plane, rdtfolder)
        self.assertEqual(len(filtered_data), 2)
        self.assertNotIn(['BPM3', 100.0, 50.0, 20.0], filtered_data)

    def test_update_bpm_data(self):
        bpmdata = {
            'BPM1': {'key1': [], 'key2': []},
            'BPM2': {'key1': [], 'key2': []}
        }
        data = [
            ['BPM1', 1.0, 0.5, 0.2],
            ['BPM2', 2.0, 1.5, 1.2]
        ]
        update_bpm_data(bpmdata, data, 'key1', 0.1)
        self.assertEqual(len(bpmdata['BPM1']['key1']), 1)
        self.assertEqual(bpmdata['BPM1']['key1'][0], [0.1, 1.0, 0.5, 0.2])

    def test_getrdt_omc3(self):
        ldb = None  # Mock or create a dummy ldb object
        modelbpmlist = ['BPM1', 'BPM2']
        bpmdata = {
            'BPM1': {'s': 0.0, 'ref': [], 'data': []},
            'BPM2': {'s': 1.0, 'ref': [], 'data': []}
        }
        ref = 'tests/test_data/ref'
        flist = ['tests/test_data/f1', 'tests/test_data/f2']
        knob = 'LHCBEAM/IP5-XING-H-MURAD'
        outputpath = 'tests/test_output'
        rdt = '0030'
        rdt_plane = 'x'
        rdtfolder = 'normal_quadrupole'
        intersectedBPMdata = getrdt_omc3(ldb, modelbpmlist, bpmdata, ref, flist, knob, outputpath, rdt, rdt_plane, rdtfolder)
        self.assertIn('BPM1', intersectedBPMdata)
        self.assertIn('BPM2', intersectedBPMdata)

if __name__ == '__main__':
    unittest.main()
