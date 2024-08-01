import os
import subprocess

def gitCmd( git_params, raise_on_error=True ):
    git_cmd = [ "git" ] + git_params
    result = subprocess.run( git_cmd, capture_output=True, text=True )
    if 0 != result.returncode:
        exn = CmdFailed( "git", git_params, result.returncode, result.stdout, result.stderr )
        if raise_on_error:
            raise exn
        else:
            print( exn )
    return result

class CmdFailed( Exception ):
    def __init__( self, cmd, params, exit_code, out, err ):
        self.cmd = cmd
        self.params = params
        self.exit_code = exit_code
        self.out = out
        self.err = err

    def __str__( self ):
        return f"ERROR. {self.cmd} cmd failed. `{' '.join( self.params )}` => {self.exit_code}. o:'{self.out}' e:'{self.err}'"

class CorncobTest:
    def __init__( self, corncob_dir ):
        self.corncob_dir = corncob_dir

    def corncob_cmd( self, params, raise_on_error=True ):
        cmd = [ "python3", f"{self.corncob_dir}{os.path.sep}git-remote-workalike-corncob.py" ] + params
        result = subprocess.run( cmd, shell=False, capture_output=True, text=True )
        if 0 != result.returncode:
            exn = CmdFailed( "corncob", params, result.returncode, result.stdout, result.stderr )
            if raise_on_error:
                raise exn
            else:
                print( exn )
        return result
