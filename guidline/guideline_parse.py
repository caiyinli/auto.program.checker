from utils.csv import *

class Command:
    def __init__(self, command, length, name, flag=None, attribute=None):
        self.command=command
        self.length = length
        self.name=name 
        self.flag=flag
        self.attribute=attribute
        self.rule_list=[]
        self.flag_dict={}

class ComapreRule:
    def __init__(self, dwordstart, dwordend, filedstart, fieldend, name, attribute, checkcond):
        self.dwordstart=dwordstart
        self.dwordend=dwordend
        self.fieldstart=filedstart
        self.fieldend=fieldend
        self.name=name
        self.attribute=attribute
        self.checkcond=checkcond

class Guidline:
    def __init__(self, guidline_file):
        self.guidline_file=guidline_file
        self.command_dict={}#command code to the command definition which include compare rules for the dword
        self._parse()
    
    #parse the guild line file to get the command info and the dword compare rule
    def _parse():
        pass
        







