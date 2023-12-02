import pcbnew
import os
import wx.aui
import wx

def get_sel():
    for x in pcbnew.GetCurrentSelection():
        if isinstance(x,pcbnew.FOOTPRINT):
            return x
        elif isinstance(x,pcbnew.PAD):
            return x.GetParent()

def get_lib(libname):
    lib = os.path.join(os.environ['KICAD7_FOOTPRINT_DIR']
                       ,libname+'.pretty')
    if os.path.isdir(lib):
        footprints = pcbnew.FootprintEnumerate(lib)
        return lib,footprints
    return None,None

# Reference https://github.com/KiCad/kicad-source-mirror/blob/master/pcbnew/pcb_edit_frame.cpp#L2104
def processTextItems(aSrc,aDest):
    aDest.SetText(aSrc.GetText())
    aDest.SetLayer(aSrc.GetLayer())
    aDest.SetVisible(aSrc.IsVisible())
    aDest.SetAttributes(aSrc)
    #This function doesn't exist in the Python bindings
    #aDest.SetFPRelativePosition(aSrc.GetFPRelativePosition())
    aDest.SetLocked( aSrc.IsLocked() )

# Reference https://github.com/KiCad/kicad-source-mirror/blob/master/pcbnew/pcb_edit_frame.cpp#L2194
def exchange_footprints(aExisting, aNew):
    board = aExisting.GetParent()
    aNew.SetParent(board)
    aNew.SetPosition(aExisting.GetPosition())
    if aNew.GetLayer() != aExisting.GetLayer():
        aNew.Flip(aNew.GetPosition(), True)
    if aNew.GetOrientation() != aExisting.GetOrientation():
        aNew.SetOrientation( aExisting.GetOrientation())
    aNew.SetLocked( aExisting.IsLocked())

    for pad in aNew.Pads():
        if pad.GetNumber() is None or not pad.IsOnCopperLayer():
            pad.SetNetCode(pcbnew.NETINFO_LIST.UNCONNECTED)
            continue
        last_pad = None
        while True:
            pad_model = aExisting.FindPadByNumber( pad.GetNumber(), last_pad )
            if pad_model is None:
                break
            if pad_model.IsOnCopperLayer():
                break
            last_pad = pad_model

        if pad_model is not None:
            pad.SetLocalRatsnestVisible( pad_model.GetLocalRatsnestVisible() )
            pad.SetPinFunction( pad_model.GetPinFunction())
            pad.SetPinType( pad_model.GetPinType())
            pad.SetNetCode( pad_model.GetNetCode() )
        else:
            pad.SetNetCode( pcbnew.NETINFO_LIST.UNCONNECTED )
    processTextItems(aExisting.Reference(),aNew.Reference())
    processTextItems(aExisting.Value(),aNew.Value())
    #TODO: Process all text items
    #TODO: Copy fields
    #TODO: Copy UUID
    aNew.SetPath(aExisting.GetPath())
    board.RemoveNative(aExisting)
    board.Add(aNew)
    aNew.ClearFlags()

def next_fp(direction):
    board = pcbnew.GetBoard()
    # TODO: Handle more than one item
    f = get_sel()
    if f is None:
        print("Nothing selected")
        return
    f.ClearSelected()
    fid = f.GetFPIDAsString()
    print(f'Selected {f.GetReference()} {fid}')
    libname,_,fpname = fid.partition(':')
    # Get the list of footprints from the library
    lib,footprints = get_lib(libname)
    i = footprints.index(fpname)
    i += direction
    if i < 0:
        i = 0
    elif i >= len(footprints):
        i = len(footprints)-1
    # Set the footprint to the next
    newfid = f'{libname}:{footprints[i]}'
    print(f'Changing to {newfid}')
    newfp = pcbnew.FootprintLoad(lib,footprints[i])
    newfp.SetFPIDAsString(newfid)
    exchange_footprints(f, newfp)
    newfp.SetSelected()
    pcbnew.Refresh()

class NextFp(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Next Footprint"
        self.category = "placement"
        self.description = "Cycles through footprints. Intended for changing resistor length while prototyping."
        self.show_toolbar_button = True# Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'simple_plugin.png') # Optional, defaults to ""
    def Run(self):
        next_fp(1)
class PrevFp(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Previous Footprint"
        self.category = "placement"
        self.description = "Cycles through footprints. Intended for changing resistor length while prototyping."
        self.show_toolbar_button = True# Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'simple_plugin.png') # Optional, defaults to ""
    def Run(self):
        next_fp(-1)

NextFp().register() # Instantiate and register to Pcbnew
PrevFp().register() # Instantiate and register to Pcbnew

def findPcbnewWindow():
    """Find the window for the PCBNEW application."""
    windows = wx.GetTopLevelWindows()
    pcbnew = [w for w in windows if "PCB Editor" in w.GetTitle()]
    if len(pcbnew) != 1:
        raise Exception("Cannot find pcbnew window from title matching!")
    return pcbnew[0]

def FindToolBar(barid = pcbnew.ID_H_TOOLBAR):
    bar = [a for a in findPcbnewWindow().GetChildren() if a.GetId() == barid]
    if len(bar) != 1:
        raise Exception("Cannot find toolbar panel from ID matching")
    return bar[0]

def FindToolId(tool):
    bar = FindToolBar()
    tools = [bar.FindToolByIndex(i) for i in range(bar.ToolCount)]
    if isinstance(tool,str):
        name = tool
    else:
        name = tool.name
    tid = [t.GetId() for t in tools if t.ShortHelp == name]
    if len(tid) != 1:
        raise Exception("Cannot find desired tool")
    return tid[0]

mainFrame = findPcbnewWindow()
next_fp_button = wx.NewId()
prev_fp_button = wx.NewId()
nfb  = FindToolId(NextFp())
pfb = FindToolId(PrevFp())
def btn_press(id):
    mainFrame.QueueEvent(wx.CommandEvent(wx.wxEVT_TOOL, id=id))
def next_fp_callback(context):
    print(context)
    btn_press(nfb)
def prev_fp_callback(context):
    print(context)
    btn_press(pfb)

accel_tbl = wx.AcceleratorTable([(wx.ACCEL_SHIFT,  ord('J'), next_fp_button )
                                 ,(wx.ACCEL_SHIFT,  ord('K'), prev_fp_button )
                                 ])
mainFrame.Bind(wx.EVT_TOOL, next_fp_callback, id=next_fp_button)
mainFrame.Bind(wx.EVT_TOOL, prev_fp_callback, id=prev_fp_button)
mainFrame.SetAcceleratorTable(accel_tbl)
print("Starting plugin NextFP")
