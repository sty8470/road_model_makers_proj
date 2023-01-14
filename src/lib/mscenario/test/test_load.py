import os
import sys
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) # mscenario가 있는 경로를 추가한다.
sys.path.append(os.path.normpath(os.path.join(current_path, '../class_defs'))) # mscenario가 있는 경로를 추가한다.

from class_defs import *
from mscenario import MScenario 

def load_test_case_001():
    mscenario = MScenario()
    mscenario.load('C:/Projects/ModelMaker/rsc/scenario/kcity_scenario')

def save_test_case_001():
    mscenario = MScenario()
    mscenario = mscenario.load('C:/Projects/ModelMaker/rsc/scenario/kcity_scenario')
    mscenario.save('C:/Projects/ModelMaker/rsc/scenario/kcity_scenario/save_test')

if __name__ == u'__main__':
    save_test_case_001()
