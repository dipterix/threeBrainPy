


class ConstantGenerator():
    '''
 ------------------------------------ Layer setups ------------------------------------
  Defines for each camera which layers are visible.
  Protocols are
    Layers:
      - 0, 2, 3: Especially reserved for main camera
      - 1, Shared by all cameras
      - 4, 5, 6: Reserved for side-cameras
      - 7: reserved for all, system reserved
      - 8: main camera only, system reserved
      - 9 side-cameras 1 only, system reserved
      - 10 side-cameras 2 only, system reserved
      - 11 side-cameras 3 only, system reserved
      - 12 side-cameras 4 only, system reserved
      - 13 all side cameras, system reserved
      - 14~31 invisible
CONSTANTS.LAYER_USER_MAIN_CAMERA_0 = 0;           // User use, main camera only
CONSTANTS.LAYER_USER_ALL_CAMERA_1 = 1;            // User use, all cameras visible
CONSTANTS.LAYER_USER_ALL_SIDE_CAMERAS_4 = 4;      // User use, all side cameras
CONSTANTS.LAYER_SYS_ALL_CAMERAS_7 = 7;            // System reserved, all cameras
CONSTANTS.LAYER_SYS_MAIN_CAMERA_8 = 8;            // System reserved, main cameras only
CONSTANTS.LAYER_SYS_CORONAL_9 = 9;                // System reserved, coronal camera only
CONSTANTS.LAYER_SYS_AXIAL_10 = 10;                 // System reserved, axial camera only
CONSTANTS.LAYER_SYS_SAGITTAL_11 = 11;              // System reserved, sagittal camera only
CONSTANTS.LAYER_SYS_ALL_SIDE_CAMERAS_13 = 13;      // System reserved, all side cameras visible
CONSTANTS.LAYER_SYS_RAYCASTER_14 = 14;               // System reserved, raycaster use
CONSTANTS.LAYER_INVISIBLE_31 = 31;                   // invisible layer, but keep rendered
------------------------------------ Global constants ------------------------------------
# reorder render depth to force renders to render objects with maximum render order first
CONSTANTS.MAX_RENDER_ORDER = 9999999;
    '''
    @property
    def LAYER_USER_MAIN_CAMERA_0(self):
        return 0
    @property
    def LAYER_USER_ALL_CAMERA_1(self):
        return 1
    @property
    def LAYER_USER_ALL_SIDE_CAMERAS_4(self):
        return 4
    @property
    def LAYER_SYS_ALL_CAMERAS_7(self):
        return 7
    @property
    def LAYER_SYS_MAIN_CAMERA_8(self):
        return 8
    @property
    def LAYER_SYS_CORONAL_9(self):
        return 9
    @property
    def LAYER_SYS_AXIAL_10(self):
        return 10
    @property
    def LAYER_SYS_SAGITTAL_11(self):
        return 11
    @property
    def LAYER_SYS_ALL_SIDE_CAMERAS_13(self):
        return 13
    @property
    def LAYER_SYS_RAYCASTER_14(self):
        return 14
    @property
    def LAYER_INVISIBLE_31(self):
        return 31
    @property
    def MAX_RENDER_ORDER(self):
        return 9999999
    
    # default slice files
    @property
    def DEFAULT_SLICE_PREFIXIES(self):
        return ["brain.finalsurfs", "synthSR.norm", "synthSR", "brain", 
                "brainmask", "brainmask.auto", "T1"]
    
    @property
    def DEFAULT_ATLAS_PREFIXIES(self):
        return ["aparc+aseg", "aparc.a2009s+aseg", "aparc.DKTatlas+aseg", "aseg"]
    
    @property
    def SUPPORTED_SPACES(self):
        return ["ras", "ras_tkr", "voxel", "mni305", "mni152"]
    @property
    def MNI305_TO_MNI152(self):
        return [
            [0.99750 , -0.00730, 0.01760 , -0.04290],
            [0.01460 , 1.00090 , -0.00240, 1.54960 ],
            [-0.01300, -0.00930, 0.99710 , 1.18400 ],
            [0.00000 , 0.00000 , 0.00000 , 1.00000 ]
        ]
    
    @property
    def SURFACE_BASE_TEXTURE_TYPES(self):
        return ["sulc", "curv", "thickness", "volume"]

    

# // Regular expressions
# CONSTANTS.REGEXP_SURFACE_GROUP    = /^Surface - (.+) \((.+)\)$/;  // Surface - pial (YAB)
# CONSTANTS.REGEXP_VOLUME_GROUP     = /^Volume - (.+) \((.+)\)$/;   // Volume - brain.finalsurfs (YAB)
# CONSTANTS.REGEXP_ELECTRODE_GROUP  = /^Electrodes \((.+)\)$/;                  // Electrodes (YAB)
# CONSTANTS.REGEXP_SURFACE          = /^([\w ]+) (Left|right) Hemisphere - (.+) \((.+)\)$/;   // Standard 141 Left Hemisphere - pial (YAB)
# CONSTANTS.REGEXP_ATLAS            = /^Atlas - ([^\(\)]+)\s\(/;  // Atlas - aparc_aseg (YAB)
# CONSTANTS.REGEXP_VOLUME           = /^(.+) \((.+)\)$/;                   // brain.finalsurfs (YAB)
# CONSTANTS.REGEXP_ELECTRODE        = /^(.+), ([0-9]+) - (.*)$/;     // YAB, 1 - pSYLV12



# Create a singleton instance
CONSTANTS = ConstantGenerator()