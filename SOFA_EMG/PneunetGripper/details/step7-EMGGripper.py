import math
import numpy as np
import csv
import os

import Sofa
import Sofa.Core


from wholeGripperController import WholeGripperController

youngModulusFingers = 500
youngModulusStiffLayerFingers = 1500

radius = 70
angle1 = 120 * math.pi / 180  # Angle between 1st and 2nd finger in radian
angle2 = 240 * math.pi / 180  # Angle between 1st and 3rd finger in radian
translateFinger1 = [0, 0, 0]
translateFinger2 = [0, radius + radius * math.sin(angle1 - math.pi / 2), radius * math.cos(angle1 - math.pi / 2)]
translateFinger3 = [0, radius + radius * math.sin(angle2 - math.pi / 2), radius * math.cos(angle2 - math.pi / 2)]
translations = [translateFinger1, translateFinger2, translateFinger3]
angles = [0, angle1, angle2]

class EMGController(Sofa.Core.Controller):

    def __init__(self, rootNode):
        Sofa.Core.Controller.__init__(self)

        self.rootNode = rootNode
        self.statusLabel = rootNode.getObject('EMGStateLabel')
        self.rmsLabel = rootNode.getObject('EMGRMSLabel')
        self.pressureLabel = rootNode.getObject('EMGPressureLabel')
        self.gripLabel = rootNode.getObject('EMGGripLabel')

        # Get the three finger pressure constraints
        self.constraints = []

        for i in range(1, 4):
            finger = rootNode.getChild('Finger' + str(i))
            constraint = finger.Cavity.getObject('SurfacePressureConstraint')
            self.constraints.append(constraint)

        # EMG simulation parameters
        self.sample_rate = 100
        self.emg_time = 0.0

        # 100 ms RMS window
        self.rms_window = int(0.1 * self.sample_rate)
        self.emg_buffer = []

        # Current EMG state
        self.last_state = ""

        # Current pressure command
        self.pressure = 0.0
        

        # Allow SOFA to send events to this controller
        self.listening = True
        # -----------------------------
        # DATA LOGGING
        # -----------------------------

        self.data_log = []

        self.log_saved = False

        self.log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "emg_grasp_data.csv"
        )

        # Get cube mechanical state
        self.cube = rootNode.getChild('Cube')
        self.cubeMO = self.cube.getObject('MechanicalObject')

    def setPressure(self, pressure):

        self.pressure = pressure

        for constraint in self.constraints:
            constraint.value = [self.pressure]



    def generateEMG(self, t):

        # Same EMG activity pattern as our previous model
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

        # Small noise
        noise = 0.02 * np.random.randn()

        # 20 Hz carrier
        carrier = np.sin(2 * np.pi * 20 * t)

        return amplitude * carrier + noise

    def onAnimateBeginEvent(self, event):

        # Advance EMG simulation time
        self.emg_time += self.rootNode.dt.value

        # Generate synthetic EMG
        emg_sample = self.generateEMG(self.emg_time)

        # Rectification
        rectified = abs(emg_sample)

        # Add sample to RMS buffer
        self.emg_buffer.append(rectified)

        if len(self.emg_buffer) > self.rms_window:
            self.emg_buffer.pop(0)

        # Calculate RMS
        rms = np.sqrt(np.mean(np.square(self.emg_buffer)))

        # -----------------------------
        # EMG CLASSIFICATION
        # -----------------------------

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

        # -----------------------------
        # EMG → PRESSURE MAPPING
        # -----------------------------

        if emg_state == "LOW":

            self.setPressure(0.0)

        elif emg_state == "MEDIUM":

            self.setPressure(0.25)

        elif emg_state == "HIGH":

            self.setPressure(0.4)

        # Print only when state changes
        if emg_state != self.last_state:

            print(
                f"EMG: {emg_state} | "
                f"RMS: {rms:.3f} | "
                f"Pressure: {self.pressure:.2f}"
            )

            self.last_state = emg_state

        if emg_state == "HIGH":
            grip_state = "GRASPING"
        else:
            grip_state = "OPEN"

        if emg_state == "HIGH":
            grip_state = "GRASPING"
        else:
            grip_state = "OPEN"

        self.statusLabel.label = f"EMG: {emg_state}"
        self.rmsLabel.label = f"RMS: {rms:.3f}"
        self.pressureLabel.label = f"PRESSURE: {self.pressure:.2f}"
        self.gripLabel.label = f"GRIP: {grip_state}"
                # -----------------------------
        # RECORD EXPERIMENT DATA
        # -----------------------------

        cube_position = self.cubeMO.position.value[0]

        cube_x = cube_position[0]
        cube_y = cube_position[1]
        cube_z = cube_position[2]

        self.data_log.append([
            round(self.emg_time, 3),
            round(rms, 4),
            emg_state,
            round(self.pressure, 4),
            grip_state,
            round(cube_x, 3),
            round(cube_y, 3),
            round(cube_z, 3)
        ])

        # Save automatically after the 10-second EMG experiment
        # -----------------------------
        # RECORD EXPERIMENT DATA
        # -----------------------------

        cube_position = self.cubeMO.position.value[0]

        cube_x = cube_position[0]
        cube_y = cube_position[1]
        cube_z = cube_position[2]

        self.data_log.append([
            round(self.emg_time, 3),
            round(rms, 4),
            emg_state,
            round(self.pressure, 4),
            grip_state,
            round(cube_x, 3),
            round(cube_y, 3),
            round(cube_z, 3)
        ])

        # Save once after 10 seconds
        if self.emg_time >= 10.0 and not self.log_saved:

            with open(self.log_file, 'w', newline='') as file:

                writer = csv.writer(file)

                writer.writerow([
                    'Time_s',
                    'RMS',
                    'EMG_State',
                    'Pressure',
                    'Grip_State',
                    'Cube_X',
                    'Cube_Y',
                    'Cube_Z'
                ])

                for row in self.data_log:
                    writer.writerow(row)

            self.log_saved = True

            print("")
            print("===================================")
            print("EMG EXPERIMENT DATA SAVED")
            print(self.log_file)
            print("Samples:", len(self.data_log))
            print("===================================")
            print("")


def createScene(rootNode):
    rootNode.addObject(
    'RequiredPlugin',
    name='Sofa.GL.Component.Rendering2D'
)
    rootNode.addObject('RequiredPlugin',
                       pluginName='SoftRobots SofaPython3')
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.AnimationLoop')  # Needed to use components [FreeMotionAnimationLoop]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Detection.Algorithm')  # Needed to use components [BVHNarrowPhase,BruteForceBroadPhase,CollisionPipeline]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Detection.Intersection')  # Needed to use components [LocalMinDistance]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Geometry')  # Needed to use components [LineCollisionModel,PointCollisionModel,TriangleCollisionModel]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Collision.Response.Contact')  # Needed to use components [CollisionResponse]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Correction')  # Needed to use components [GenericConstraintCorrection,UncoupledConstraintCorrection]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Constraint.Lagrangian.Solver')  # Needed to use components [BlockGaussSeidelConstraintSolver]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Engine.Select')  # Needed to use components [BoxROI]  
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.IO.Mesh')  # Needed to use components [MeshOBJLoader,MeshSTLLoader,MeshVTKLoader]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.LinearSolver.Direct')  # Needed to use components [SparseLDLSolver]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.LinearSolver.Iterative')  # Needed to use components [CGLinearSolver]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Mapping.Linear')  # Needed to use components [BarycentricMapping]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Mapping.NonLinear')  # Needed to use components [RigidMapping]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Mass')  # Needed to use components [UniformMass]  
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.ODESolver.Backward')  # Needed to use components [EulerImplicitSolver]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Setting')  # Needed to use components [BackgroundSetting]  
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.FEM.Elastic')  # Needed to use components [TetrahedronFEMForceField]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.SolidMechanics.Spring')  # Needed to use components [RestShapeSpringsForceField]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.StateContainer')  # Needed to use components [MechanicalObject]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Constant')  # Needed to use components [MeshTopology]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Topology.Container.Dynamic')  # Needed to use components [TetrahedronSetTopologyContainer]
    rootNode.addObject('RequiredPlugin', name='Sofa.Component.Visual')  # Needed to use components [VisualStyle]  
    rootNode.addObject('RequiredPlugin', name='Sofa.GL.Component.Rendering3D')  # Needed to use components [OglModel,OglSceneFrame]

    rootNode.addObject('VisualStyle',
                       displayFlags='showVisualModels hideBehaviorModels hideCollisionModels '
                                    'hideBoundingCollisionModels hideForceFields '
                                    'showInteractionForceFields hideWireframe')
    rootNode.gravity.value = [-9810, 0, 0]
    rootNode.dt = 0.01
    rootNode.addObject('FreeMotionAnimationLoop')
    rootNode.addObject('BlockGaussSeidelConstraintSolver', tolerance=1e-7, maxIterations=1000)
    rootNode.addObject('CollisionPipeline')
    rootNode.addObject('BruteForceBroadPhase')
    rootNode.addObject('BVHNarrowPhase')
    rootNode.addObject('CollisionResponse', response='FrictionContactConstraint', responseParams='mu=0.6')
    rootNode.addObject('LocalMinDistance', name='Proximity', alarmDistance=5, contactDistance=1)

    rootNode.addObject('BackgroundSetting', color=[0, 0.168627, 0.211765, 1.])
    rootNode.addObject('OglSceneFrame', style='Arrows', alignment='TopRight')
    rootNode.addObject(
        'OglLabel',
        name='EMGStateLabel',
        label='EMG: LOW',
        fontsize=18,
        x=20,
        y=30,
        selectContrastingColor=True
    )

    rootNode.addObject(
        'OglLabel',
        name='EMGRMSLabel',
        label='RMS: 0.000',
        fontsize=18,
        x=20,
        y=55,
        selectContrastingColor=True
    )

    rootNode.addObject(
        'OglLabel',
        name='EMGPressureLabel',
        label='PRESSURE: 0.00',
        fontsize=18,
        x=20,
        y=80,
        selectContrastingColor=True
    )

    rootNode.addObject(
        'OglLabel',
        name='EMGGripLabel',
        label='GRIP: OPEN',
        fontsize=18,
        x=20,
        y=105,
        selectContrastingColor=True
    )

    ##########################################
    # Plane
    ##########################################
    plane = rootNode.addChild('Plane')
    plane.addObject('MeshOBJLoader', name='loader', filename='data/mesh/floorFlat.obj',
                    rotation=[0, 0, 270], scale=10, translation=[-122, 0, 0])
    plane.addObject('MeshTopology', src='@loader')
    plane.addObject('MechanicalObject', src='@loader')
    plane.addObject('TriangleCollisionModel')
    plane.addObject('LineCollisionModel')
    plane.addObject('PointCollisionModel')
    plane.addObject('OglModel', name='Visual', src='@loader', color=[1, 0, 0, 1])

    ##########################################
    # Cube
    ##########################################
    cube = rootNode.addChild('Cube')
    cube.addObject('EulerImplicitSolver')
    cube.addObject('CGLinearSolver', threshold=1e-5, tolerance=1e-5, iterations=50)
    cube.addObject('MechanicalObject', template='Rigid3', position=[-100, 70, 0, 0, 0, 0, 1])
    cube.addObject('UniformMass', totalMass=0.001)
    cube.addObject('UncoupledConstraintCorrection')

    # collision
    cubeCollis = cube.addChild('Collision')
    cubeCollis.addObject('MeshOBJLoader', name='loader', filename='data/mesh/smCube27.obj', scale=6)
    cubeCollis.addObject('MeshTopology', src='@loader')
    cubeCollis.addObject('MechanicalObject')
    cubeCollis.addObject('TriangleCollisionModel')
    cubeCollis.addObject('LineCollisionModel')
    cubeCollis.addObject('PointCollisionModel')
    cubeCollis.addObject('RigidMapping')

    # visualization
    cubeVisu = cube.addChild('Visu')
    cubeVisu.addObject('MeshOBJLoader', name='loader', filename='data/mesh/smCube27.obj')
    cubeVisu.addObject('OglModel', name='Visual', src='@loader', color=[0.0, 0.1, 0.5], scale=6.2)
    cubeVisu.addObject('RigidMapping')

    for i in range(3):
        ##########################################
        # Finger Model
        ##########################################
        finger = rootNode.addChild('Finger' + str(i + 1))
        finger.addObject('EulerImplicitSolver', name='odesolver', rayleighStiffness=0.1, rayleighMass=0.1)
        finger.addObject('SparseLDLSolver', template="CompressedRowSparseMatrixd")
        finger.addObject('MeshVTKLoader', name='loader', filename='data/mesh/pneunetCutCoarse.vtk',
                         rotation=[360 - angles[i] * 180 / math.pi, 0, 0], translation=translations[i])
        finger.addObject('MeshTopology', src='@loader', name='container')
        finger.addObject('MechanicalObject', name='tetras', template='Vec3', showIndices=False, showIndicesScale=4e-5)
        finger.addObject('UniformMass', totalMass=0.04)
        finger.addObject('TetrahedronFEMForceField', template='Vec3', name='FEM', method='large', poissonRatio=0.3,
                         youngModulus=youngModulusFingers)
        if i == 0:
            boxROI = finger.addObject('BoxROI', name='boxROI', box=[-10, 0, -20, 0, 30, 20], doUpdate=False)
            boxROISubTopo = finger.addObject('BoxROI', name='boxROISubTopo', box=[-100, 22.5, -8, -19, 28, 8], strict=False)
        finger.addObject('RestShapeSpringsForceField',
                         points=boxROI.indices.linkpath,
                         stiffness=1e12, angularStiffness=1e12)
        finger.addObject('GenericConstraintCorrection')

        # Sub topology
        modelSubTopo = finger.addChild('SubTopology')
        modelSubTopo.addObject('TetrahedronSetTopologyContainer', position='@../loader.position',
                               tetrahedra=boxROISubTopo.tetrahedraInROI.linkpath, name='container')
        modelSubTopo.addObject('TetrahedronFEMForceField', template='Vec3', name='FEM', method='large',
                               poissonRatio=0.3, youngModulus=youngModulusStiffLayerFingers - youngModulusFingers)

        # Constraint
        cavity = finger.addChild('Cavity')
        cavity.addObject('MeshSTLLoader', name='loader', filename='data/mesh/pneunetCavityCut.stl',
                         translation=translations[i], rotation=[360 - angles[i] * 180 / math.pi, 0, 0])
        cavity.addObject('MeshTopology', src='@loader', name='topo')
        cavity.addObject('MechanicalObject', name='cavity')
        cavity.addObject('SurfacePressureConstraint', name='SurfacePressureConstraint', template='Vec3',
                         value=0.0001,
                         triangles='@topo.triangles', valueType='pressure')
        cavity.addObject('BarycentricMapping', name='mapping', mapForces=False, mapMasses=False)

        # Collision
        collisionFinger = finger.addChild('Collision')
        collisionFinger.addObject('MeshSTLLoader', name='loader', filename='data/mesh/pneunetCut.stl',
                                  translation=translations[i], rotation=[360 - angles[i] * 180 / math.pi, 0, 0])
        collisionFinger.addObject('MeshTopology', src='@loader', name='topo')
        collisionFinger.addObject('MechanicalObject')
        collisionFinger.addObject('TriangleCollisionModel')
        collisionFinger.addObject('LineCollisionModel')
        collisionFinger.addObject('PointCollisionModel')
        collisionFinger.addObject('BarycentricMapping')

        # Visualization
        modelVisu = finger.addChild('Visu')
        modelVisu.addObject('MeshSTLLoader', name='loader', filename='data/mesh/pneunetCut.stl')
        modelVisu.addObject('OglModel', src='@loader', color=[0.7, 0.7, 0.7, 0.6], translation=translations[i],
                            rotation=[360 - angles[i] * 180 / math.pi, 0, 0])
        modelVisu.addObject('BarycentricMapping')

    rootNode.addObject(WholeGripperController(node=rootNode))

    # EMG controller
    rootNode.addObject(EMGController(rootNode))

    return rootNode
