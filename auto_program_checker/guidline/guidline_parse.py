
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
import logging
import csv as csv
#command class for checklist parser
class Command:
    def __init__(self, command='', length=0, fieldname='', fieldset='', flag=None, attribute=None):
        self.command=command
        self.length = int(length, 16)
        self.fieldname=fieldname 
        self.fieldset=fieldset 
        self.flag=flag
        self.attribute=attribute
        self.dw_rules=[]
        self.flag_dict={}
    
    #convert hexadecimal dword into binary dword 
    def get_binary_dword(self, hex_dword):
        return str(bin(int(hex_dword,16))[2:].zfill(32))
        
    def __repr__(self) -> str:
        def target_str(field): 
            if field is None or field == '':
                return "None"
            else:
                return field
        #print command level info
        cmd_info = "'Command:' {}, 'Length:' {}, 'FiledSet:' {}, 'FiledName:' {}, 'Flag:' {}, 'Attribute:' {} ".format(target_str(self.command),target_str(self.length),target_str(self.fieldset),target_str(self.fieldname), target_str(self.flag),target_str(self.attribute))
        #print compare rule level info
        for rule in self.dw_rules:
            cmd_info += "\n"
            cmd_info += rule.__repr__()
        return cmd_info 

class ComapreRule:
    def __init__(self, dwordstart=None, dwordend=None, bitstart=None, bitend=None, flag=None,fieldset=None, fieldname=None, subfieldname=None, attribute=None, checkcond=None):
        self.dwordstart=int(dwordstart)
        self.dwordend=int(dwordend)
        self.bitstart=int(bitstart)
        self.bitend=int(bitend)
        self.flag=flag
        self.fieldset=fieldset
        self.fieldname=fieldname
        self.subfieldname=subfieldname
        self.attribute=attribute
        self.checkcond=checkcond

    def __repr__(self) -> str:
        def target_str(field): 
            if field is None or field == '':
                return "None"
            else:
                return field

        return "'DwordStart:' {}, 'DwordEnd:' {}, 'BitStart:'{}, 'BitEnd:' {}, 'FieldSet:' {}, FieldName:'{}, 'SubFieldName:'{}, 'Flag:'{}, 'Attribute:'{}, 'CheckCond:' {}".format(target_str(self.dwordstart), target_str(self.dwordend),target_str(self.bitstart),target_str(self.bitend),target_str(self.fieldset),target_str(self.fieldname),target_str(self.subfieldname), target_str(self.flag),target_str(self.attribute),target_str(self.checkcond))

class Guidline:
    def __init__(self, guidline_file):
        self.guidline_file=guidline_file
        #print(self.guidline_file)
        self.command_dict={}#command code to the command definition which include compare rules for the dword
        self._parse()

    #parse the guild line file to get the command info and the dword compare rule
    #guidline file format as following:
    #if the command column is not null, it means the begin of the command
    #else it is a compare rule of this command
    #Command    Length  DwordStart  DwordEnd    FieldStart  FieldEnd    Name    Flag    Attribute   CheckCond   Comment
    #73ca0001   0x3                 VVCP_VD_CONTROL_STATE               
    #73c00004   0x6                 VVCP_PIPE_MODE_SELECT               
    #73c10003   0x5                 VVCP_SURFACE_STATE  surface_state_number    dynamic     
    #73c30002   0x4                 VVCP_IND_OBJ_BASE_ADDR_STATE                
    #                   1       0   31  address low     check_null      
    #                   2       0   31  address high        waiver      
    #                   3       1   6   mocs        waiver      
    def _parse(self):
        with open(self.guidline_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows=[]
            for row in reader:
                rows.append(row)
                i=0
                while i < len(rows): 
                    row = rows[i]
                    #print(row)
                    if row['Command'] !='':#find a new command
                        command = Command(command=row['Command'][2:7],length=row['Length'], fieldname=row['FieldName'], fieldset=row['FieldSet'],flag=row['Flag'], attribute=row['Attribute'])
                    #parse the rule of this command
                    while i+1 < len(rows) and rows[i+1]['Command'] == '':
                        i = i + 1
                        row = rows[i]
                        rule = ComapreRule(dwordstart=row['DWStart'], dwordend=row['DWEnd'], bitstart=row['BitStart'], bitend=row['BitEnd'], fieldset=row['FieldSet'],fieldname=row['FieldName'], subfieldname=row['SubFieldName'], flag=row['Flag'], attribute=row['Attribute'], checkcond=row['CheckCond'])
                        command.dw_rules.append(rule)
                    self.command_dict[command.command] = command
                    #print(command)
                    i = i + 1 

def main():
    parser = ArgumentParser(description="This is a tool to parse checklist",formatter_class=RawTextHelpFormatter)
    parser.add_argument("-c", "--checklist", type=str, default="", help='The driver programming checklist')
    args = parser.parse_args()
    guid=Guidline(args.checklist)
    for key in guid.command_dict:
        print(guid.command_dict[key])
    
if __name__ == "__main__":
    main()

