import os
import subprocess

class CorncobTest:
    def __init__( self, corncob_dir ):
        self.corncob_dir = corncob_dir

    def corncob_cmd( self, params ):
        cmd = [ "python3", f"{self.corncob_dir}{os.path.sep}git-remote-workalike-corncob.py" ] + params
        return subprocess.run( cmd, shell=False, capture_output=True, text=True )

