import pcbnew
import os
import wx

def get_sel(context = None):
    sel = pcbnew.GetCurrentSelection()
    for x in sel:
        print(x)
        if isinstance(x,pcbnew.FOOTPRINT):
            return x
        elif isinstance(x,pcbnew.PAD):
            return x.GetParent()
        else:
            print('not pad or footprint')

def next_fp(direction):
    # The entry function of the plugin that is executed on user action
    board = pcbnew.GetBoard()
    # TODO: Handle more than one item
    f = get_sel()
    if f is None:
        return
    fid = f.GetFPIDAsString()
    print(f'Selected {f.GetReference()} {fid}')
    libname,_,fpname = fid.partition(':')
    # Get the list of footprints from the library
    lib = os.path.join(os.environ['KICAD7_FOOTPRINT_DIR']
                       ,libname+'.pretty')
    footprints = os.listdir(lib)
    footprints = [x.partition('.kicad_mod')[0] for x in footprints]
    # TODO: Sort by numbers like the Footprint Library Browser does
    footprints.sort()
    i = footprints.index(fpname)
    i += direction
    if i < 0:
        i = 0
    elif i >= len(footprints):
        i = len(footprints)-1
    # Set the footprint to the next
    newfp = f'{libname}:{footprints[i]}'
    print(f'Changing to {newfp}')
    f.SetFPIDAsString(newfp) 
    pcbnew.FootprintLoad(libname,footprints[i])
    # FIXME: Update footprint from library
    pass

def next_fp_callback(context):
    next_fp(1)

def prev_fp_callback(context):
    next_fp(-1)

def findPcbnewWindow():
    """Find the window for the PCBNEW application."""
    windows = wx.GetTopLevelWindows()
    pcbnew = [w for w in windows if "PCB Editor" in w.GetTitle()]
    if len(pcbnew) != 1:
        raise Exception("Cannot find pcbnew window from title matching!")
    return pcbnew[0]

class NextFp(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "next_footprint"
        self.category = "placement"
        self.description = "Cycles through footprints. Intended for changing resistor length while prototyping."
        self.show_toolbar_button = False # Optional, defaults to False
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'simple_plugin.png') # Optional, defaults to ""

    def Run(self):
        mainFrame = findPcbnewWindow()
        next_fp_button = wx.NewId()
        prev_fp_button = wx.NewId()
        test_button = wx.NewId()
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_SHIFT,  ord('J'), next_fp_button )
                                         ,(wx.ACCEL_SHIFT,  ord('K'), prev_fp_button )
                                         ,(wx.ACCEL_SHIFT,  ord('M'), test_button)])
        mainFrame.Bind(wx.EVT_TOOL, next_fp_callback, id=next_fp_button)
        mainFrame.Bind(wx.EVT_TOOL, prev_fp_callback, id=prev_fp_button)
        mainFrame.Bind(wx.EVT_TOOL, get_sel, id=test_button)
        mainFrame.SetAcceleratorTable(accel_tbl)


NextFp().register() # Instantiate and register to Pcbnew
