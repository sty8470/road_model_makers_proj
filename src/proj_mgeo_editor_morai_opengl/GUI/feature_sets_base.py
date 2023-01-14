class BaseFeatureSet():
    def __init__(self, canvas):
        self.canvas = canvas

    def getNodeSet(self):
        return self.canvas.getNodeSet()


    def getLinkSet(self):
        return self.canvas.getLinkSet()


    def getTSSet(self):
        return self.canvas.getTSSet()


    def getTLSet(self):
        return self.canvas.getTLSet()


    def getJunctionSet(self):
        return self.canvas.getJunctionSet() 


    def getRoadSet(self):
        return self.canvas.getRoadSet()
