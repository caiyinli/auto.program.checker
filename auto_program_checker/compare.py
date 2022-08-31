from errno import ENETRESET
import os
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import logging
from vcs_dump_parser.dump_parser import DumpParser,RowParser
from guidline.guideline_parse import Guidline

format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format_str)
logger = logging.getLogger(__name__)

def parse_args():
    """
    Helper function parsing the command line options
    @retval ArgumentParser
    """
    parser = ArgumentParser(description="This is a tool "                                        
                                        "\n############################################################################# \n",
                                        formatter_class=RawTextHelpFormatter)

    parser.add_argument("-d", "--driverdump", type=str, default="", help='The driver vcsring dump file')
    parser.add_argument("-g", "--gritsdump", type=str, default="", help='The grits vcsring dump file')
    parser.add_argument("-c", "--checklist", type=str, default="", help='The driver programming checklist')
    parser.add_argument("-w", "--workmode", type=int, default=0, help='The workmode, 1 is debug mode and 0 is execution mode')
    parser.add_argument("-m", "--mmc", default=False, action="store_true",
                        help="Enable memory management comparation.")
    return parser.parse_args()
   

def cmd_compare(cmd_driver, cmd_grits, mmc=False):
    #if cmd_driver.original_row == cmd_grits.original_row:#exactly same 
    #    return True
    dw_length = cmd_grits.command_rule.length #get the dw length need to be compared 
    print(dw_length)
    dws_driver = ''
    dws_grits = ''
    for i in range(1, dw_length+1):#dword[0] is the command code 
        dws_grits += RowParser.get_binary_dword(cmd_grits.dwords[i])
        dws_driver += RowParser.get_binary_dword(cmd_driver.dwords[i])
        
    #print(dws_driver, dws_grits)    
    mydict={'surface_state_num':1}
    test = 'surface_state_num>1'
    test = test.replace('surface_state_num', str(mydict['surface_state_num']))
    print(eval(test))
    return True

def slide_compare(slide_driver, slide_grits, mmc=False):
    for i, rp_driver in enumerate(slide_driver.rp_list):
        rp_grits = slide_grits.rp_list[i]
        expected = cmd_compare(rp_driver, rp_grits, mmc)
        if not expected:
            return False

def main():
    args = parse_args()
    guid=Guidline(args.checklist)
    driver_dp =  DumpParser(args.driverdump, checklist=guid)
    grits_dp = DumpParser(args.gritsdump, checklist=guid)
    if len(grits_dp.frame_list) != len(driver_dp.frame_list):        
        logger.warning("There are {} frames in grits dump  {} while only {} frames in driver dump {}".format(len(grits_dp.frame_list), args.gritsdum, len(driver_dp.frame_list), args.driverdump))
    for i,frame_driver in enumerate(driver_dp.frame_list):
        #compare the command sequence 
        frame_grits = grits_dp.frame_list[i]
        if frame_driver.cmd_list != frame_grits.cmd_list:
            logger.error("The command sequence of frame {} in grits dums is not same to the frame {} in driver dump".format(frame_grits.cid, frame_driver.cid))  
        #compare the slide one by one
        for j, slide_driver in enumerate(frame_driver.slides):
            slide_grits = frame_grits.slides[j]
            slide_compare(slide_driver, slide_grits, args.mmc)
  

if __name__ == "__main__":
    main()

