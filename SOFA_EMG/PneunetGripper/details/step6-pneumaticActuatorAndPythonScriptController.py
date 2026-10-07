import Sofa
import numpy as np
from fingerController import FingerController


class EMGController(Sofa.Core.Controller):

    def __init__(self, rootNode):
        Sofa.Core.Controller.__init__(self)
        self.rootNode = rootNode

        self.fingerNode = rootNode.getChild('Finger')
        self.pressureConstraint = self.fingerNode.Cavity.getObject(
            'SurfacePressureConstraint'
        )

        self.pressure = 0.0
        self.time = 0.0
        self.listening = True

        self.sample_rate = 100
        self.emg_time = 0.0

        self.rms_window = int(0.1 * self.sample_rate)
        self.emg_buffer = []
        self.last_state = ""

    def setPressure(self, pressure):
        self.pressure = pressure
        self.pressureConstraint.value = [self.pressure]

    def generateEMG(self, t):
        if t < 2.0:
            amplitude = 0.08
        elif t < 5.0:
            amplitude = 0.30
        elif t < 6.5:
            amplitude = 0.08
        elif t < 9.0:
            amplitude = 0.90
        else:
            amplitude = 0.08

        noise = 0.02 * np.random.randn()
        carrier = np.sin(2 * np.pi * 20 * t)

        return amplitude * carrier + noise

    def onAnimateBeginEvent(self, event):
        self.emg_time += self.rootNode.dt.value
        emg_sample = self.generateEMG(self.emg_time)
        rectified = abs(emg_sample)

        self.emg_buffer.append(rectified)

        if len(self.emg_buffer) > self.rms_window:
            self.emg_buffer.pop(0)

        rms = np.sqrt(np.mean(np.square(self.emg_buffer)))

        if self.last_state == "":
            if rms < 0.15:
                emg_state = "LOW"
            elif rms < 0.55:
                emg_state = "MEDIUM"
            else:
                emg_state = "HIGH"

        elif self.last_state == "LOW":
            if rms >= 0.55:
                emg_state = "HIGH"
            elif rms >= 0.15:
                emg_state = "MEDIUM"
            else:
                emg_state = "LOW"

        elif self.last_state == "MEDIUM":
            if rms >= 0.55:
                emg_state = "HIGH"
            elif rms < 0.12:
                emg_state = "LOW"
            else:
                emg_state = "MEDIUM"

        elif self.last_state == "HIGH":
            if rms < 0.50:
                emg_state = "MEDIUM"
            else:
                emg_state = "HIGH"

        if emg_state == "LOW":
            self.setPressure(0.0)

        elif emg_state == "MEDIUM":
            self.setPressure(0.5)

        elif emg_state == "HIGH":
            self.setPressure(1.0)

        if emg_state != self.last_state:

            print(f"EMG: {emg_state} | RMS: {rms:.3f} | Pressure: {self.pressure:.1f}")

            self.last_state = emg_state


def createScene(rootNode):
    rootNode.addObject('VisualStyle', displayFlags='showForceFields showBehaviorModels')
    rootNode.addObject('RequiredPlugin', pluginName='SoftRobots SofaPython3')

    rootNode.addObject('RequiredPlugin', name='Sofa.Component.AnimationLoop')  # Needed to use components [FreeMotionAnimationLoop]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Correction')  # Needed to use components [LinearSolverConstraintCorrection]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Solver')  # Needed to use components [BlockGaussSeidelConstraintSolver]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Engine.Select')  # Needed to use components [BoxROI]  
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')  # Needed to use components [MeshSTLLoader,MeshVTKLoader]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.LinearSolver.Direct')  # Needed to use components [SparseLDLSolver]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Mapping.Linear')  # Needed to use components [BarycentricMapping]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Mass')  # Needed to use components [UniformMass]  
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.ODESolver.Backward')  # Needed to use components [EulerImplicitSolver]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.FEM.Elastic')  # Needed to use components [TetrahedronFEMForceField]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.Spring')  # Needed to use components [RestShapeSpringsForceField]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.StateContainer')  # Needed to use components [MechanicalObject]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Constant')  # Needed to use components [MeshTopology]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Visual')  # Needed to use components [VisualStyle]  
    rootNode.addObject('RequiredPlugin', name='Sofa.GUI.Component')  # Needed to use components [AttachBodyButtonSetting] 
    
    rootNode.dt = 0.01
    rootNode.gravity.value = [-9810, 0, 0]
    rootNode.addObject('AttachBodyButtonSetting', stiffness=10)
    rootNode.addObject('FreeMotionAnimationLoop')
    rootNode.addObject('BlockGaussSeidelConstraintSolver', tolerance=1e-7, maxIterations=1000)

    finger = rootNode.addChild('Finger')
    finger.addObject('EulerImplicitSolver', rayleighStiffness=0.1, rayleighMass=0.1)
    finger.addObject('SparseLDLSolver', template='CompressedRowSparseMatrixd')
    finger.addObject('MeshVTKLoader', name='loader', filename='data/mesh/pneunetCutCoarse.vtk')
    finger.addObject('MeshTopology', src='@loader', name='container')
    finger.addObject('MechanicalObject', name='tetras', template='Vec3', showObject=True, showObjectScale=1)
    finger.addObject('TetrahedronFEMForceField', template='Vec3', name='FEM', method='large', poissonRatio=0.3,
                     youngModulus=500)
    finger.addObject('UniformMass', totalMass=0.04)
    boxROISubTopo = finger.addObject('BoxROI', name='boxROISubTopo', box=[-100, 22.5, -8, -19, 28, 8], strict=False)
    boxROI = finger.addObject('BoxROI', name='boxROI', box=[-10, 0, -20, 0, 30, 20], drawBoxes=True)
    finger.addObject('RestShapeSpringsForceField', points=boxROI.indices.linkpath, stiffness=1e12, angularStiffness=1e12)
    finger.addObject('GenericConstraintCorrection')

    modelSubTopo = finger.addChild('SubTopology')
    modelSubTopo.addObject('MeshTopology', position='@loader.position', tetrahedra=boxROISubTopo.tetrahedraInROI.linkpath,
                           name='container')
    modelSubTopo.addObject('TetrahedronFEMForceField', template='Vec3', name='FEM', method='large', poissonRatio=0.3,
                           youngModulus=1500)

    cavity = finger.addChild('Cavity')
    cavity.addObject('MeshSTLLoader', name='cavityLoader', filename='data/mesh/pneunetCavityCut.stl')
    cavity.addObject('MeshTopology', src='@cavityLoader', name='cavityMesh')
    cavity.addObject('MechanicalObject', name='cavity')
    cavity.addObject('SurfacePressureConstraint', name='SurfacePressureConstraint', template='Vec3', value=1,
                     triangles='@cavityMesh.triangles', valueType='pressure')
    cavity.addObject('BarycentricMapping', name='mapping', mapForces=False, mapMasses=False)

    rootNode.addObject(FingerController(rootNode))
    rootNode.addObject(EMGController(rootNode))
