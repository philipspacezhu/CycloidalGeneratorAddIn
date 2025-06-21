import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ... import config
import traceback
import math

def deg_range(start, stop, step):
    r = start
    while r <= stop:
        yield r
        r += step

def cos(angle):
    return math.cos(math.radians(angle))
def sin(angle):
    return math.sin(math.radians(angle))
 
app = adsk.core.Application.get()
ui = app.userInterface


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cycloidGeneratorCmd'
CMD_NAME = 'Cycloid Drive Generator'
CMD_Description = 'A Fusion Add-in to Generate Cycloid Drives from user-defined parameters.'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED

# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()

# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.
    # Set the default length units for the command inputs, usually mm.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits

    # Number of Roller Pins Input field, default 11, Reduction ratio = pin_count - 1.
    inputs.addIntegerSpinnerCommandInput('pin_count', 'Number of Roller Pins', 0, 101, 1, 11)

    # Cycloidal Disk Radius value input field, default 50
    default_value = adsk.core.ValueInput.createByString('50')
    inputs.addValueInput('cycloid_radius', 'Cycloid Disc Radius', defaultLengthUnits, default_value)
    
    # Roller Pin Radius Input field, default 5 
    default_value = adsk.core.ValueInput.createByString('5')
    inputs.addValueInput('pin_radius', 'Pin Radius', defaultLengthUnits, default_value)

    # Eccentricity value input field, default 2.5, need to find way to make this half of the pin radius.
    default_value = adsk.core.ValueInput.createByString('2.5')
    inputs.addValueInput('eccentricity', 'Eccentricity = Roller Pin Radius / 2', defaultLengthUnits, default_value)
    
    #Disk extrustion extent length input field, default 5.
    default_value = adsk.core.ValueInput.createByString('5')
    inputs.addValueInput('disk_extent_length', 'Disk Extrude Extent Length', defaultLengthUnits, default_value)

    #Roller pin extrusion extent length input field, default 10.
    default_value = adsk.core.ValueInput.createByString('10')
    inputs.addValueInput('roller_extent_length', 'Roller Pins Extrude Extent Length', defaultLengthUnits, default_value)

    #Output Roller Pin Shaft Offset Radius value input field, default 5

    # Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)


# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    # TODO ******************************** Your code here ********************************
 
    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs

    # Access the value of 'pin_count' (integer spinner input)
    pin_radius_input = inputs.itemById('pin_radius')
    pin_radius = pin_radius_input.value

    cycloid_radius_input = inputs.itemById('cycloid_radius')
    cycloid_radius = cycloid_radius_input.value

    # Access the value of 'cycloid_radius' (value input)
    pin_count_input = inputs.itemById('pin_count')
    pin_count = pin_count_input.value

    # Access the value of 'pin_radius' (value input)
    eccentricity_input = inputs.itemById('eccentricity')
    eccentricity = eccentricity_input.value

    # Access the value of 'disk_extent_length' (value input) 
    disk_extent_length_input = inputs.itemById('disk_extent_length')
    disk_extent_length = disk_extent_length_input.value

    # Access the value of 'disk_extent_length' (value input) 
    roller_extent_length_input = inputs.itemById('roller_extent_length')
    roller_extent_length = roller_extent_length_input.value

    # === Place your sketch creation code here ===
    doc = app.activeDocument
    design = app.activeProduct
    rootComp = design.rootComponent
    # Create a new sketch on the XZ plane of the root component.
    cycloid_sketches = rootComp.sketches
    cycloid_sketch = cycloid_sketches.add(rootComp.xZConstructionPlane)

    # TODO *** Add your code to create the cycloid drive here. ***
    #Using some code and math from RoTechnic's design of a cycloidal drive in Python and Fusion 360 https://github.com/roTechnic/CycloidalDesign
    rolling_circle_radius = cycloid_radius / pin_count
    reduction_ratio = pin_count - 1
    cycloid_base_radius = rolling_circle_radius * reduction_ratio

    last_point = None
    line = None

    lines = []

    for angle in deg_range(0, 360, 5):
        x = (cycloid_base_radius + rolling_circle_radius) * cos(angle)
        y = (cycloid_base_radius + rolling_circle_radius) * sin(angle)
 
        point_x = x + (rolling_circle_radius - eccentricity) * cos(pin_count*angle)
        point_y = y + (rolling_circle_radius - eccentricity) * sin(pin_count*angle)

        if angle == 0:
            # Create the first point
            last_point = adsk.core.Point3D.create(point_x, point_y, 0)
        else:
            # Create a line from the last point to the current point
            line = cycloid_sketch.sketchCurves.sketchLines.addByTwoPoints(last_point, adsk.core.Point3D.create(point_x, point_y, 0))
            last_point = line.endSketchPoint
            lines.append(line)

        # Watch the curve get drawn in the sketch.
        app.activeViewport.refresh()
    curves = cycloid_sketch.findConnectedCurves(lines[0])
            
    # # Create the offset for the roller pins.
    sketch_direction_point = adsk.core.Point3D.create(0, 0, 0)
    offset_curves = cycloid_sketch.offset(curves, sketch_direction_point, pin_radius + 0.4)

    # Create a sketch for the eccentric shaft in the disk.
    eccentric_shaf_sketches = rootComp.sketches
    eccentric_shaft_sketch = eccentric_shaf_sketches.add(rootComp.xZConstructionPlane)
    sketchCircles = eccentric_shaft_sketch.sketchCurves.sketchCircles
    eccentric_point = adsk.core.Point3D.create(eccentricity, 0, disk_extent_length)
    eccentric_circle = sketchCircles.addByCenterRadius(eccentric_point, pin_radius)
    
    # Create a sketch for a roller pin at the edge of the cycloidal disk with the specified offset.
    roller_sketches = rootComp.sketches
    roller_sketch = roller_sketches.add(rootComp.xZConstructionPlane)
    roller_circles = roller_sketch.sketchCurves.sketchCircles
    roller_pin_center = adsk.core.Point3D.create(cycloid_radius - eccentricity, 0, 0) 
    roller_pin_circle = roller_circles.addByCenterRadius(roller_pin_center, pin_radius)

    # Create a sketch for the roller pin plate.
    origin_point = adsk.core.Point3D.create(0, 0, 0)
    roller_plate_sketches = rootComp.sketches
    roller_plate_sketch = roller_plate_sketches.add(rootComp.xZConstructionPlane)
    roller_plate_circle = roller_plate_sketch.sketchCurves.sketchCircles.addByCenterRadius(origin_point, cycloid_radius + pin_radius)

    # Create a sketch for the throughhole in the centre of the roller disk.
    throughhole_sketches = rootComp.sketches
    throughhole_sketch = throughhole_sketches.add(rootComp.xZConstructionPlane)
    throughhole_circle = throughhole_sketch.sketchCurves.sketchCircles.addByCenterRadius(origin_point, pin_radius + 0.2)

    # Create a sketch for the output  roller pins
    output_roller_sketches = rootComp.sketches
    output_roller_sketch = output_roller_sketches.add(rootComp.xZConstructionPlane)
    output_roller_circles = output_roller_sketch.sketchCurves.sketchCircles
    output_roller_center = adsk.core.Point3D.create(cycloid_radius / 2.25, 0, disk_extent_length)
    output_roller_circle = output_roller_circles.addByCenterRadius(output_roller_center, pin_radius)

    # Extrude the cycloidal disk based on user provided disk_extent_length.
    cycloid_prof = cycloid_sketch.profiles.item(1)
    # Create an extrusion input
    cycloid_extrudes = rootComp.features.extrudeFeatures
    extInput = cycloid_extrudes.createInput(cycloid_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    # Define that the extent is a distance extent of disk extent length.
    distance = adsk.core.ValueInput.createByReal(disk_extent_length)
    extInput.setDistanceExtent(False, distance)
    # Create the extrusion.
    ext = cycloid_extrudes.add(extInput)

    #Cut the hole for the eccentric shaft in the cycloidal disk.
    eccentric_prof = eccentric_shaft_sketch.profiles.item(0)
    eccentric_shaft_extrudes = rootComp.features.extrudeFeatures
    cutInput = eccentric_shaft_extrudes.createInput(eccentric_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    # Define that the extent is a distance extent of user provided disk_extent_length.
    distance = adsk.core.ValueInput.createByReal(-disk_extent_length)
    cutInput.setDistanceExtent(False, distance)
    # Create the cut.
    cut = eccentric_shaft_extrudes.add(cutInput)

    # Extrude roller plate under roller pin ring.
    roller_plate_prof = roller_plate_sketch.profiles.item(0)
    # Create an extrusion input
    roller_plate_extrudes = rootComp.features.extrudeFeatures 
    extInput = roller_plate_extrudes.createInput(roller_plate_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    # Define that the extent is a distance extent same as the disk extent length.
    distance = adsk.core.ValueInput.createByReal(-disk_extent_length)
    extInput.setDistanceExtent(False, distance)
    # Create the extrusion.
    ext = roller_plate_extrudes.add(extInput)

    #Extrude user provided pin_count # of roller pins 360 deg around the cycloidal disk.
    rollers_prof = roller_sketch.profiles.item(0)
    # Create an extrusion input
    roller_extrudes = rootComp.features.extrudeFeatures
    extInput = roller_extrudes.createInput(rollers_prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    # Define that the extent is a distance extent of user provided roller_extent_length.
    distance = adsk.core.ValueInput.createByReal(roller_extent_length)
    extInput.setDistanceExtent(False, distance)
    # Create the extrusion.
    ext = roller_extrudes.add(extInput)
    # Get the body created by extrusion
    roller_body = rootComp.bRepBodies.item(2)
    # Create input entities for circular pattern
    inputEntites = adsk.core.ObjectCollection.create()
    inputEntites.add(roller_body)
    # Get Y axis for circular pattern
    yAxis = rootComp.yConstructionAxis
    # Create the input for circular pattern
    circularFeats = rootComp.features.circularPatternFeatures
    circularFeatInput = circularFeats.createInput(inputEntites, yAxis)
    # Set the quantity of the elements
    circularFeatInput.quantity = adsk.core.ValueInput.createByReal(pin_count)
    # Set the angle of the circular pattern
    circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    # Set symmetry of the circular pattern
    circularFeatInput.isSymmetric = True
    # Create the circular pattern 
    circularFeat = circularFeats.add(circularFeatInput)

    #Cut output roller pins 360 deg into the cycloidal disk.
    # Create a sketch the axis in the centre of the eccentric disk.
    eccentric_axis_sketches = rootComp.sketches
    eccentric_axis_sketch = eccentric_axis_sketches.add(rootComp.xYConstructionPlane)
    lines = eccentric_axis_sketch.sketchCurves.sketchLines
    line1 = lines.addByTwoPoints(adsk.core.Point3D.create(eccentricity, 0, 0), adsk.core.Point3D.create(eccentricity, 1, 0))
    roller_pin_center = adsk.core.Point3D.create(cycloid_radius, 0, 0)
    output_rollers_prof = output_roller_sketch.profiles.item(0)
    # Create an extrusion input
    output_roller_extrudes = rootComp.features.extrudeFeatures
    cutInput = output_roller_extrudes.createInput(output_rollers_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    # Define that the extent is a distance extent of user provided roller_extent_length.
    distance = adsk.core.ValueInput.createByReal(-disk_extent_length)
    cutInput.setDistanceExtent(False, distance)
    # Create the extrusion.
    cut = output_roller_extrudes.add(cutInput)
    # Create input entities for circular pattern
    inputEntites = adsk.core.ObjectCollection.create()
    inputEntites.add(cut)
    circularFeats = cut.parentComponent.features.circularPatternFeatures
    circularFeatInput = circularFeats.createInput(inputEntites, line1)
    # Set the quantity of the elements
    circularFeatInput.quantity = adsk.core.ValueInput.createByReal((pin_count - 1)/2)
    # Set the angle of the circular pattern
    circularFeatInput.totalAngle = adsk.core.ValueInput.createByString('360 deg')
    # Set symmetry of the circular pattern
    circularFeatInput.isSymmetric = True
    # Create the circular pattern 
    circularFeat = circularFeats.add(circularFeatInput)

    # Cut the hole for the throughhole in the roller plate.
    throughhole_prof = throughhole_sketch.profiles.item(0)
    throughhole_extrudes = rootComp.features.extrudeFeatures
    cutInput = throughhole_extrudes.createInput(throughhole_prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    # Define that the extent is a distance extent of user provided disk_extent_length.
    distance = adsk.core.ValueInput.createByReal(-disk_extent_length)
    cutInput.setDistanceExtent(False, distance)
    # Create the cut.
    cut = throughhole_extrudes.add(cutInput)


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs
    
    # Verify the validity of the input values. This controls if the OK button is enabled or not.
    valueInput = inputs.itemById('value_input')
    if valueInput.value >= 0:
        args.areInputsValid = True
    else:
        args.areInputsValid = False
        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
