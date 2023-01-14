from common import *

class TrafficLight():
    def __init__(self):
        self.index = 0
        self.state = 0
        self.deltaTime = 0

    def parse(self, json_data):
        self.index = json_data['index']
        self.state = json_data['state']
        self.deltaTime = json_data['deltaTime']

    def to_dict(self):
        dict = {
            'index': self.index,
            'state': self.state,
            'deltaTime': self.deltaTime
        }

        return dict