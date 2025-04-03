import adsk.core, adsk.fusion
import traceback
import os

app = adsk.core.Application.get()
ui = app.userInterface

CMD_ID = "SelectByIdentical"
CMD_NAME = "Select By Identical"
CMD_Description = "select common parts by shape and size"
IS_PROMOTED = True
WORKSPACE_ID = "FusionSolidEnvironment"
PANEL_ID = "SelectPanel"
COMMAND_BESIDE_ID = "SelectionFilterCommand"
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")
SelectedDefault = [0, "Bodies"]
handlers = []
SelectedList = []


def run(context):
    try:
        InitAddIn()

    except:
        ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


def stop(context):
    # ui = None

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


def InitAddIn():
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Create a button command definition.
        cmdDefs = ui.commandDefinitions
        cmdDef = cmdDefs.addButtonDefinition(
            CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER
        )

        # Connect to the commandCreated event.
        commandEventHandler = CommandEventHandler()
        cmdDef.commandCreated.add(commandEventHandler)
        handlers.append(commandEventHandler)

        # Get the Actions panel in the Manufacture workspace.
        workSpace = ui.workspaces.itemById(WORKSPACE_ID)
        addInsPanel = workSpace.toolbarPanels.itemById(PANEL_ID)

        cmdControl = addInsPanel.controls.addCommand(cmdDef, COMMAND_BESIDE_ID, False)
        cmdControl.isPromotedByDefault = True
        cmdControl.isPromoted = True

    except:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


class CommandEventHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        # adsk.core.Application.get().log(args.firingEvent.name)
        try:
            global handlers
            SelectedList.clear()
            EventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = EventArgs.command

            onExecute = MyExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute)

            onPreview = MyPreviewHandler()
            cmd.executePreview.add(onPreview)
            handlers.append(onPreview)

            onInputChanged = MyInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            handlers.append(onInputChanged)

            inputs = cmd.commandInputs
            Dropdown = inputs.addDropDownCommandInput(
                "SelectObject", "Select Object", 1
            )
            Dropdown.listItems.add("Bodies", False)
            Dropdown.listItems.add("Componants", False)
            Dropdown.listItems.item(SelectedDefault[0]).isSelected = True
            Selection = inputs.addSelectionInput("Selection", "Selection", "")
            Selection.addSelectionFilter(SelectedDefault[1])
            Selection.setSelectionLimits(1, 0)

            onCommandTerminated = MyCommandTerminatedHandler()
            ui.commandTerminated.add(onCommandTerminated)
            handlers.append(onCommandTerminated)

        except:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))


class MyCommandTerminatedHandler(adsk.core.ApplicationCommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.ApplicationCommandEventArgs):
        # adsk.core.Application.get().log(args.firingEvent.name)
        for i in SelectedList:

            sels: adsk.core.Selections = ui.activeSelections
            sels.clear
            sels.add(i)
        SelectedList.clear()


class MyCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CommandEventArgs):
        adsk.core.Application.get().log(args.firingEvent.name)
        adsk.terminate()


class MyExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CommandEventArgs):
        # adsk.core.Application.get().log(args.firingEvent.name)

        inputs: adsk.core.CommandInputs = args.command.commandInputs
        Selection: adsk.core.SelectionCommandInput = inputs.itemById("Selection")
        Entity = Selection.selection(Selection.selectionCount - 1).entity
        design: adsk.fusion.Design = app.activeProduct
        rootComp: adsk.fusion.Component = design.rootComponent

        for i in range(Selection.selectionCount):
            entity = Selection.selection(i).entity
            SelectedList.append(entity)


class MyPreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args: adsk.core.CommandEventArgs):
        # adsk.core.Application.get().log(args.firingEvent.name)
        args.command.executePreview
        global SelectedDefault
        inputs: adsk.core.CommandInputs = args.command.commandInputs
        Object: adsk.core.DropDownControl = inputs.itemById("SelectObject")
        Selection: adsk.core.SelectionCommandInput = inputs.itemById("Selection")
        Entity = Selection.selection(Selection.selectionCount - 1).entity
        design: adsk.fusion.Design = app.activeProduct
        rootComp: adsk.fusion.Component = design.rootComponent

        if Object.selectedItem.name == "Bodies":

            SelectedDefault[0] = 0
            SelectedDefault[1] = "Bodies"
            Entity: adsk.fusion.BRepBody
            for i in rootComp.bRepBodies:
                if i.isSolid:
                    if (
                        abs(i.volume - Entity.volume) < 0.001
                        and abs(i.area - Entity.area) < 0.001
                    ):
                        Selection.addSelection(i)

            for i in rootComp.allOccurrences:
                for x in i.bRepBodies:
                    if x.isSolid:
                        if (
                            abs(x.volume - Entity.volume) < 0.001
                            and abs(x.area - Entity.area) < 0.001
                        ):
                            Selection.addSelection(x)

        elif Object.selectedItem.name == "Componants":
            SelectedDefault[0] = 1
            SelectedDefault[1] = "Occurrences"
            Entity: adsk.fusion.Occurrence
            for i in rootComp.allOccurrences:
                if i.bRepBodies.count != 0:
                    if i.bRepBodies[0].isSolid:
                        if (
                            abs(i.bRepBodies[0].volume - Entity.bRepBodies[0].volume)
                            < 0.001
                            and abs(i.bRepBodies[0].area - Entity.bRepBodies[0].area)
                            < 0.001
                        ):
                            Selection.addSelection(i)


class MyInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, eventArgs):
        Args = adsk.core.InputChangedEventArgs.cast(eventArgs)
        inputs = Args.inputs

        input = Args.input
        Object: adsk.core.DropDownControl = inputs.itemById("SelectObject")
        Selection: adsk.core.SelectionCommandInput = inputs.itemById("Selection")

        if input.id == "SelectObject":

            Selection.clearSelectionFilter()
            Selection.clearSelection()

            if Object.selectedItem.name == "Bodies":
                Selection.addSelectionFilter("SolidBodies")
            elif Object.selectedItem.name == "Componants":
                Selection.addSelectionFilter("Occurrences")
                g = 6
