from audioop import bias
import cmd
import code
from operator import indexOf
import os 
import sys
from tkinter.tix import CheckList
from xmlrpc.client import FastParser
#sys.path.append("d:\\APC\\auto.program.checker\\auto_program_checker\\")
#sys.path.append("d:\\APC\\auto.program.checker\\auto_program_checker\\guidline")
#print(sys.path)

#e.g. #row="00434  00000380  01ff800400327000  12  33c1  CMD_VVCP_SURFACE_STATE     73c10003  0000007f  20000040  00000000  00000000"
class RowParser:
    def __init__(self, cmd_log, command_rule) -> None:
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
        self.code_index = cols.index(key)
        c_ind = self.code_index
        self.name = cols[c_ind-1]
        self.dwords.append(key)
        #assert(self.name == self.command_rule.name)
        assert(self.command_rule.fieldname in self.name)
        self.cmd_code = key
        while c_ind < len(cols):
            self.dwords.append(cols[c_ind])
            c_ind += 1
        #assert(len(self.dwords)==self.command_rule.length)     

class SlideParser:
    def __init__(self, rp_list) -> None:
        self.rp_list = rp_list
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
                   self.flags[dw_rule.flag] =  binary_dw[dw_rule.bitstart:dw_rule.bitend+1]             
        self.flags['surface_state_num'] = surface_state_num
        #print(self.flags)

class FrameParser:
    def __init__(self, rows, cid, checklist=None) -> None:
        self.rows = rows
        self.cid = cid
        self.slides = []
        self.cmd_list = [] #used to check the command sequence order
        self.mi_rows = [] #MI_FORCE_WAKEUP, MI_FLUSH_DW
        self.checklist = checklist     
        self._parse()

    def _parse(self):
        #import pdb 
        #pdb.set_trace()
        slide_rows = [] 
        slide_start = False
        for row in self.rows:
            cols = row.split()                   
            if cols[6][:5] in self.checklist.command_dict.keys():#this is a target command line  
                    key = cols[6][:5]
                    row = row.replace(cols[6], key)    
                    self.cmd_list.append(key)
                    row_parser = RowParser(row, self.checklist.command_dict[key])
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
                            self.slides.append(SlideParser(slide_rows))
                    elif slide_start:
                        slide_rows.append(row_parser)
                    else:
                        self.mi_rows.append(row_parser)   
            
    def __repr__(self) -> str:
        frame = self.cid
        for row in self.rows:
            frame += row 
            frame += "\n"
        frame +="<\Workload>\n"
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
            cid = ""
            for line in f.readlines():
                if line.startswith("<Workload"):                    
                    in_frame =  True
                    rows=[]
                    cid = line.strip()
                elif in_frame and not line.startswith("</Workload"):
                    rows.append(line)                     
                elif in_frame and line.startswith("</Workload"):
                    self.frame_list.append(FrameParser(rows=rows,cid=cid, checklist=self.checklist))
                    in_frame = False
                   
if __name__ == "__main__":
    pass
    #dp =  DumpParser("D:\\VVC_Grits_Fulsim_Dump\\VVC_Fulsim_d_VCS\\test.log")#VcsRingInfo_0_0_Verbose.txt")
    #for frame in dp.frame_list:
    #    pass#print(frame)