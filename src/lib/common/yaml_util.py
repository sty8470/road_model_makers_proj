import yaml
import sys
import os
current_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(current_path)
sys.path.append(os.path.normpath(os.path.join(current_path, '../'))) 
sys.path.append(os.path.normpath(os.path.join(current_path, '../../'))) 

def createYaml(data, file_full_path):
    with open(file_full_path, 'w') as outfile:
        yaml_file = yaml.dump(data, outfile, default_flow_style=False, sort_keys=False)
    return yaml_file






if __name__ == u'__main__':
    dic = dict(a='A', b='B', c= dict(ca='CA'))
    createYaml(dic)