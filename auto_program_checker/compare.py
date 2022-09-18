from calendar import c
import os
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import logging
from tkinter import N
from vcs_dump_parser.dump_parser import DumpParser,RowParser
from guidline.guidline_parse import Guidline

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
    parser.add_argument("-m", "--mmc", type=str, default="off", help="Enable memory management comparation[on, off].")
    return parser.parse_args()

def equal_bits(bit_start, bit_end, grits_bits, driver_bits):
    for i in range(bit_start, bit_end):
        if grits_bits[i] != driver_bits[i]:
            return False
    return True

def nonull_bits(bit_start, bit_end, driver_bits):
    for i in range(bit_start, bit_end):
         if driver_bits[i] == '1':
                return True  
    return False


def cmd_compare(cmd_driver, cmd_grits, flags, mmc='off'):
    def modify_bits(bits_str, start, end, target='0'):
        bits_list = list(bits_str)
        for bi in range(start, end+1):
            bits_list[bi] = target
        return ''.join(bits_list)

    print(cmd_driver)
    print(cmd_grits)
    if '73c10' in cmd_driver.cmd_code:
        import pdb 
        pdb.set_trace()
    dw_length = cmd_grits.command_rule.length #get the dw length need to be compared 
    dws_driver = ''
    dws_grits = ''
    expected = True
    for i in range(0, dw_length):#dword[0] is the command code 
        dws_grits += RowParser.get_binary_dword(cmd_grits.dwords[i])
        dws_driver += RowParser.get_binary_dword(cmd_driver.dwords[i])

    #don't need to compare the last 12 bits in the dwords[0]
    dws_grits = modify_bits(dws_grits, 20, 31)
    dws_driver = modify_bits(dws_driver, 20, 31)

    #exactly match     
    if dws_driver == dws_grits:
        return True
    #for dw_rule in cmd_grits.command_rule.dw_rules:
    #    print(dw_rule)
    #precess the exception filed bits according to the dwords rule in checklist  
    for dw_rule in cmd_grits.command_rule.dw_rules: 
        #Attention: the bit in rule is from right to left while we need access character in str from left to right
        bit_left = 0 #the start bit to compare specified by dw_rule for dws_driver/dws_grits
        bit_right = 0   #the right bit of end bit to compare specified by dw_rule for dws_driver/dws_grits
        if dw_rule.bitstart == 0 and dw_rule.bitend == 31:
            bit_left = (dw_rule.dwordstart) * 32 
            bit_right =(dw_rule.dwordend) * 32
        else:
            assert(dw_rule.dwordstart == dw_rule.dwordend)
            bit_left = (dw_rule.dwordstart+1) * 32 - dw_rule.bitend - 1
            bit_right = (dw_rule.dwordstart+1) * 32 - dw_rule.bitstart -1
        enable_check_cond = True
        print(dw_rule)
        
        #print(dw_rule.checkcond)
        if dw_rule.checkcond:
            expression = dw_rule.checkcond #e.g, surface_state_num>1
            print(expression)           
            if 'MMC' in expression:
                print(expression)
                mmc_value = expression.split('(')[0].split('==')[1].lower()
                if mmc_value != mmc:
                    enable_check_cond = False
                
            else:
                for item in expression.split():
                    if item in flags:
                        expression = expression.replace(item, str(flags[item]))
                enable_check_cond = eval(expression) 
       
        print(dw_rule.attribute)
        attribute = dw_rule.attribute
        if attribute == 'waiver':
            expected = True 
        elif attribute == 'match' and enable_check_cond:
            expected = equal_bits(bit_left, bit_right, dws_grits, dws_driver)
        elif attribute == 'match_otherwise_non_null' and enable_check_cond:
            expected = equal_bits(bit_left, bit_right, dws_grits, dws_driver)
        elif attribute == 'match_otherwise_non_null' and not enable_check_cond:
            expected = nonull_bits(bit_left, bit_right, dws_driver)
        elif attribute == 'non_null' and enable_check_cond:
            expected = nonull_bits(bit_left, bit_right, dws_driver)
        elif attribute == "match_onlyif_non_zero" and enable_check_cond:
            expected = equal_bits(bit_left, bit_right, dws_grits, dws_driver)
        if not expected:
            return expected
        #set the bit to 0 between bitstart and bitend since these bits has been processed
        dws_driver =  modify_bits(dws_driver, bit_left, bit_right)
        dws_grits = modify_bits(dws_grits, bit_left, bit_right)
    #The exception fileds bits has been set to 0, other fileds bits should be exactly match
    expected = (dws_driver==dws_grits)
    return expected

def slide_compare(slide_driver, slide_grits, mmc='off'):
    for i, rp_driver in enumerate(slide_driver.rp_list):
        rp_grits = slide_grits.rp_list[i]
        expected = cmd_compare(rp_driver, rp_grits, slide_grits.flags, mmc)
        if not expected:
            logger.error("The xxxxxxxxxxxxxxxxxxxxx")#ToDo
            return False

def main():
    args = parse_args()
    guid=Guidline(args.checklist)
    driver_dp =  DumpParser(args.driverdump, checklist=guid)
    grits_dp = DumpParser(args.gritsdump, checklist=guid)
    if len(grits_dp.frame_list) != len(driver_dp.frame_list):        
        logger.warning("There are {} frames in grits dump  {} while only {} frames in driver dump {}".format(len(grits_dp.frame_list), args.gritsdump, len(driver_dp.frame_list), args.driverdump))
    for i,frame_driver in enumerate(driver_dp.frame_list):         
        frame_grits = grits_dp.frame_list[i]

        #compare the commend sequence 
        #if len(frame_driver.cmd_list) != len(frame_grits.cmd_list):
        #    logger.error("The command sequence {} of frame {} in grits dums is not same to the sequence {} in frame {} in driver dump".format(frame_driver.cmd_list, frame_grits.frame_index, frame_grits.cmd_list, frame_driver.frame_index))          
        for ind, driver_cmd_code in enumerate(frame_driver.cmd_list):
            grits_cmd_code = frame_grits.cmd_list[ind]
            if driver_cmd_code != grits_cmd_code:
               cond1 = (driver_cmd_code == '13000' or driver_cmd_code == '13010')
               cond2 = (grits_cmd_code == '13000' or grits_cmd_code == '13010')
               if not (cond1 and cond2):
                  logger.info("The {} th driver frame:{}".format(i, frame_driver.cmd_list))
                  logger.info("The {} th grits fame:{}".format(i, frame_grits.cmd_list))
                  logger.error("The command in frame {} of driver dump is {} while it is {} in frame {} of grits dump".format(i, driver_cmd_code, grits_cmd_code, i))
        
        assert(len(frame_driver.mi_rows) == len(frame_grits.mi_rows))
        assert(len(frame_driver.mi_rows) == 3) #MI_FORCE_WAKEUP, MI_FLUSH_DW(13000), and MI_FLUSH_DW(13010)

        #compare the MI_FORCE_WAKEUP and MI_FLUSH_DW in the begin of frame 
        cmd_compare(frame_driver.mi_rows[0], frame_grits.mi_rows[0],None)#MI_FORCE_WAKEUP
        cmd_compare(frame_driver.mi_rows[1], frame_grits.mi_rows[1],None)#MI_FLUSH_DW
        #compare the slide one by one
        for j, slide_driver in enumerate(frame_driver.slides):
            slide_grits = frame_grits.slides[j]
            slide_compare(slide_driver, slide_grits, args.mmc)
        cmd_compare(frame_driver.mi_rows[2], frame_grits.mi_rows[2],None)#MI_FLUSH_DW
        
if __name__ == "__main__":
    main()

