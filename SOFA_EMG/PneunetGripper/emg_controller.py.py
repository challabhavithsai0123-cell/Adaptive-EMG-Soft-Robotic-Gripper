import Sofa


class EMGController(Sofa.Core.Controller):

    def __init__(self, rootNode):
        Sofa.Core.Controller.__init__(self)
        self.rootNode = rootNode

        self.fingerNode = rootNode.getChild("Finger")
        self.pressureConstraint = (
            self.fingerNode.Cavity.getObject("SurfacePressureConstraint")
        )

        self.pressure = 0.0

    def setPressure(self, pressure):
        self.pressure = pressure
        self.pressureConstraint.value = [self.pressure]