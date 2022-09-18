import os 
import sys
sys.path.append('d:\\APC\\auto.program.checker\\auto_program_checker\\')
print(sys.path)
from guidline.guidline_parse import Guidline
#e.g. #row="00434  00000380  01ff800400327000  12  33c1  CMD_VVCP_SURFACE_STATE     73c10003  0000007f  20000040  00000000  00000000"
class RowParser:
    def __init__(self, cmd_log, command_rule):
        self.cmd_code=None
        self.code_index=-1
        self.filedname = None
        self.command_rule = command_rule
        self.dwords=[]
        self.original_row = cmd_log 
        self._parse()

    def __repr__(self) -> str:
        return self.original_row

    #convert hexadecimal dword into binary dword 
    @staticmethod
    def get_binary_dword(hex_dword):
        return str(bin(int(hex_dword,16))[2:].zfill(32))

    def _parse(self):
        cols =  self.original_row.split()
        key =  self.command_rule.command
        self.code_index = 6
        c_ind = self.code_index 
        self.name = cols[5]
        #self.dwords.append(cols[6])
        #assert(self.name == self.command_rule.name)
        assert(self.command_rule.fieldname in self.name)
        self.cmd_code = key
        while c_ind < len(cols):
            self.dwords.append(cols[c_ind])
            c_ind += 1
        #assert(len(self.dwords)==self.command_rule.length)     

class SlideParser:
    def __init__(self, rp_list,slide_index) -> None:
        self.rp_list = rp_list
        self.slide_index=slide_index
        self.flags = {}
        self._parse()

    def _parse(self):#mark flags info
        surface_state_num = 0 
        for rp in self.rp_list:
            #print(rp)
            if rp.command_rule.flag == 'surface_state_num': # mark the command flag
                surface_state_num += 1
            for dw_rule in rp.command_rule.dw_rules:
                if dw_rule.flag:
                   assert(dw_rule.dwordstart==dw_rule.dwordend)
                   binary_dw = str(rp.get_binary_dword(rp.dwords[dw_rule.dwordstart]))                              
                   self.flags[dw_rule.flag] =  str(int(binary_dw[31 - dw_rule.bitend : 31 - dw_rule.bitstart + 1],2))            
                   if dw_rule.bitend != dw_rule.bitstart:
                       print(binary_dw, dw_rule.bitend, dw_rule.bitstart, self.flags)
        self.flags['surface_state_num'] = surface_state_num
        #print(self.flags)
        #print(self.flags)
    def __repr__(self) -> str:
        res = ''
        for rp in self.rp_list:
            res += rp.__repr__() 
            res += '\n'
        return res

class FrameParser:
    def __init__(self, rows, frame_index, checklist=None) -> None:
        self.rows = rows
        self.frame_index = frame_index
        self.slides = []
        self.cmd_list = [] #used to check the command sequence order
        self.rp_list = []
        self.mi_rows = [] #MI_FORCE_WAKEUP, MI_FLUSH_DW
        self.checklist = checklist     
        self._parse()

    def _parse(self):
        #import pdb 
        #pdb.set_trace()
        slide_start = False
        slide_index=0
        for row in self.rows:
            cols = row.split()                   
            if cols[6][:5] in self.checklist.command_dict.keys():#this is a target command line  
                    key = cols[6][:5]
                    #row = row.replace(cols[6], key)                       
                    row_parser = RowParser(row, self.checklist.command_dict[key])                    
                    self.cmd_list.append(key)
                    self.rp_list.append(row_parser)                                         
                        
                    #a new slide start              
                    if key == '73ca0' and not slide_start: #CMD_VVCP_VD_CONTROL_STATE 
                        slide_rows = []
                        slide_start = True
                        slide_rows.append(row_parser)
                    elif key == '77800':#CMD_VD_PIPELINE_FLUSH                        
                        slide_start = False
                        slide_rows.append(row_parser)
                        #print(len(slide_rows))
                        if len(slide_rows) != 2:
                            #print(slide_rows)
                            self.slides.append(SlideParser(slide_rows,slide_index))
                            slide_index += 1
                    elif slide_start:
                        slide_rows.append(row_parser)
                    else:
                        self.mi_rows.append(row_parser)   
                    print(self.cmd_list[-1])
                    if (key == '13000' or key == '13010') and self.cmd_list[-2] == '77800':
                        break #the frame end when meet MI_FLUSH_DW and the last cmd is CMD_VD_PIPELINE_FLUSH       

    def __repr__(self) -> str:
        frame = ""
        for row in self.rows:
            frame += row 
            frame += "\n"
        return frame

class DumpParser:
    def __init__(self, dump_file, checklist=None) -> None:
        self.dump_file=dump_file 
        self.frame_list=[]
        self.checklist = checklist
        self._parse()

    def _parse(self):
        with open(self.dump_file) as f:
            in_frame=False
            rows=[]
            frame_index = 0        
            #import pdb
            #pdb.set_trace()
            for line in f.readlines():
                if line.startswith("<Workload"):                    
                    in_frame =  True
                    rows=[]                    
                elif in_frame and not line.startswith("</Workload"):
                    rows.append(line)                     
                elif in_frame and line.startswith("</Workload"):
                    candiate_frame = FrameParser(rows=rows,frame_index=frame_index, checklist=self.checklist)
                    if len(candiate_frame.cmd_list) > 0:
                        self.frame_list.append(candiate_frame)
                        frame_index += 1
                    in_frame = False
                   
if __name__ == "__main__":
    pass
    gp = Guidline("D:\\APC\\auto.program.checker\\auto_program_checker\\config\\Emuless_VVC_checker_list.clean.csv")#
    dp =  DumpParser("D:\\VVC_Grits_Fulsim_Dump\\VVC_Fulsim_d_VCS\\test.log", checklist=gp)#VcsRingInfo_0_0_Verbose.txt")
    for frame in dp.frame_list:
        for slide in frame.slides:
            for rp in slide.rp_list:
                print(rp)
        for mi in frame.mi_rows:
            print(mi)