from mimetypes import common_types
import compare
import guidline.guidline_parse as gp 
import compare as comapre
import vcs_dump_parser.dump_parser as dp

import unittest
import os

class TestAPC(unittest.TestCase):
    def setUp(self) -> None:
        ck_list_file = "Emuless_VVC_checker_list.clean.csv" 
        driverdump = "driver_dump.txt"
        gritsdump = "grits_dump.txt" 
        file_path = os.path.join(os.getcwd(), "test_config")
        driverdump = os.path.join(file_path, driverdump)
        gritsdump = os.path.join(file_path, gritsdump)
        ck_list_file = os.path.join(file_path, ck_list_file)
        self.ck_list = gp.Guidline(ck_list_file)
        self.driver_dp =  dp.DumpParser(driverdump, checklist=self.ck_list)
        self.grits_dp = dp.DumpParser(gritsdump, checklist=self.ck_list)

    def test_checklist_parser(self):
        self.assertEqual(len(self.ck_list.command_dict), 16)
        self.assertIn('0e800', self.ck_list.command_dict)
        self.assertIn('13000', self.ck_list.command_dict)
        self.assertIn('13010', self.ck_list.command_dict)
        self.assertEqual(self.ck_list.command_dict['73ca0'].dw_rules, [])
        self.assertEqual(len(self.ck_list.command_dict['73c00'].dw_rules), 1)
        self.assertEqual(self.ck_list.command_dict['73c00'].dw_rules[0].bitstart, 24)

    def test_dump_parser(self):
        self.assertEqual(len(self.grits_dp.frame_list), 1)
        self.assertEqual(len(self.grits_dp.frame_list[0].mi_rows), 3)
        self.assertEqual(len(self.driver_dp.frame_list[0].cmd_list), 15)
        cmd_list = ['0e800', '13000', '73ca0', '73c00', '73c10', '73c20', '73c30', '73c40', '73d00', '73d40', '73e00', '73d50', '73ca0', '77800', '13010']
        self.assertAlmostEqual(self.driver_dp.frame_list[0].cmd_list, cmd_list)
        self.assertAlmostEqual(len(self.grits_dp.frame_list[0].slides),1)
        self.assertEqual(len(self.grits_dp.frame_list[0].slides[0].rp_list),12)
        flags = self.grits_dp.frame_list[0].slides[0].flags
        self.assertEqual(flags['surface_state_num'], 1)
        self.assertAlmostEqual(flags['sps_ladf_enabled_flag'], '0')
    
    def test_compare(self):
        str1 = '0000000000010100'
        str2 = '0000000000010101'
        res =  comapre.equal_bits(0, 15, str1, str2) 
        self.assertEqual(res, False)
        res = comapre.equal_bits(0, 10, str1, str2) 
        self.assertEqual(res, True)
        res = compare.nonull_bits(1, 14, str1)
        self.assertEqual(res, True)
        res = comapre.nonull_bits(0, 10, str1) 
        self.assertEqual(res, False)
        new_str = compare.modify_bits(str1, 11, 15)
        self.assertEqual(new_str, '0000000000000000')
        error_list_debug = []
        error_list_exe = []
        error_list_mmc_off = []
        for i,frame_driver in enumerate(self.driver_dp.frame_list):         
            frame_grits = self.grits_dp.frame_list[i]
            for j, slide_driver in enumerate(frame_driver.slides):
                slide_grits = frame_grits.slides[j]
                compare.slide_compare(i, j, slide_driver, slide_grits, error_list_debug, True, 'on')
                compare.slide_compare(i, j, slide_driver, slide_grits, error_list_exe, False, 'on')
                compare.slide_compare(i, j, slide_driver, slide_grits, error_list_mmc_off, True, 'off')
        self.assertEqual(len(error_list_exe), 1)
        self.assertAlmostEqual(len(error_list_debug), 6)
        self.assertAlmostEqual(len(error_list_mmc_off), 5)

                
        

if __name__ == '__main__':
    unittest.main()