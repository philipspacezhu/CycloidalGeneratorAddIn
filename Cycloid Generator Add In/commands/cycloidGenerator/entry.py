import adsk.core
import os
from ...lib import fusionAddInUtils as futil
from ... import config
import traceback
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

    # Create a value input field and set the default using 1 unit of the default length unit.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('2.5')
    inputs.addValueInput('pin_radius', 'Pin Radius', defaultLengthUnits, default_value)

    # Create a value input field and set the default using 1 unit of the default length unit.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('50')
    inputs.addValueInput('pin_circle_radius', 'Pin Cricle Radius', defaultLengthUnits, default_value)

    # Create a value input field and set the default using 1 unit of the default length unit.
    defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    default_value = adsk.core.ValueInput.createByString('5')
    inputs.addValueInput('extent_length', 'Extrude Extent Length', defaultLengthUnits, default_value)  

    # Create an integer slider value input.
    inputs.addIntegerSpinnerCommandInput('pin_count', 'Number of Roller Pins', 0, 20, 1, 5)
    
    # TODO Connect to the events that are needed by this command.
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
    pin_radius = pin_radius_input.value  # This will be an float value

    pin_circle_radius_input = inputs.itemById('pin_circle_radius')
    pin_circle_radius = pin_circle_radius_input.value  # This will be an float value

    pin_count_input = inputs.itemById('pin_count')
    pin_count = pin_count_input.value  # This will be an integer

    # Access the value of 'extent_length' (value input)
    extent_length_input = inputs.itemById('extent_length')
    extent_length = extent_length_input.value  # This will be a float value

    # === Place your sketch creation code here ===
    # Example: create a new sketch, draw circles, etc.
    doc = app.activeDocument
    design = app.activeProduct
    rootComp = design.rootComponent
    # Create a new sketch on the XZ plane of the root component.
    sketches = rootComp.sketches
    xzPlane = rootComp.xZConstructionPlane
    sketch = sketches.add(xzPlane)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(adsk.core.Point3D.create(pin_circle_radius,0,0), pin_radius)

    # Get the profile defined by the circle.
    prof = sketch.profiles.item(0)
    # Create an extrusion input
    extrudes = rootComp.features.extrudeFeatures
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

    # Define that the extent is a distance extent of extent_length cm.
    distance = adsk.core.ValueInput.createByReal(extent_length)
    extInput.setDistanceExtent(False, distance)

    # Create the extrusion.
    ext = extrudes.add(extInput)
    
    # Get the body created by extrusion
    body = rootComp.bRepBodies.item(0)
    
    # Create input entities for circular pattern
    inputEntites = adsk.core.ObjectCollection.create()
    inputEntites.add(body)
    
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
