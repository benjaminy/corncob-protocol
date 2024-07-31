import tempfile
import os
import sys
import subprocess
from corncob_test_utils import CorncobTest

def main():

    corncob_dir = os.getenv( "CORNCOB_DIR" )
    if corncob_dir == None:
        print( "ERROR. CORNCOB_DIR env var not defined" )
        return 1

    test_utils = CorncobTest( corncob_dir )

    with ( tempfile.TemporaryDirectory() as alice_local,
           tempfile.TemporaryDirectory() as alice_remote,
           tempfile.TemporaryDirectory() as bob_local,
           tempfile.TemporaryDirectory() as bob_remote ):
        print( f'Alice local: {alice_local}  Alice remote: {alice_remote}  Bob local: {bob_local}  Bob remote: {bob_remote}' )

        os.chdir( alice_local )

        git_cmd = [ "git", "init" ]
        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
        if 0 != result.returncode:
            print( f"ERROR. git init {result.returncode} {result.stdout}" )
            return result.returncode

        with open( "hi_bob.txt", "w" ) as file:
            file.write( "Hi there Bob!" )

        git_cmd = [ "git", "add", "hi_bob.txt" ]
        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
        if 0 != result.returncode:
            print( f"ERROR. git add {result.returncode} {result.stdout}" )
            return result.returncode

        git_cmd = [ "git", "commit", "-m", "greeting" ]
        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
        if 0 != result.returncode:
            print( f"ERROR. git add {result.returncode} {result.stdout}" )
            return result.returncode

        result = subprocess.run( [ "git", "status", "-v" ], capture_output=True, text=True )
        print( f"ALICE STATUS {result.stdout}" )

        result = test_utils.corncob_cmd( [ "add", "remote_blah", f"file://{alice_remote}" ] )
        if 0 != result.returncode:
            print( f"ERROR. corncob add {result.returncode} {result.stdout} {result.stderr}" )
            return result.returncode

        result = test_utils.corncob_cmd( [ "push", "remote_blah" ] )
        if 0 != result.returncode:
            print( f"ERROR. corncob push {result.returncode} {result.stdout}" )
            return result.returncode

        result = subprocess.run( [ "ls", alice_remote ], capture_output=True, text=True )
        print( result.stdout )

        os.chdir( bob_local )

        result = test_utils.corncob_cmd( [ "clone", "a_team_alice", f"file://{alice_remote}" ] )
        if 0 != result.returncode:
            print( f"ERROR. corncob clone {result.returncode} {result.stdout} {result.stderr}" )
            return result.returncode

        result = subprocess.run( [ "git", "status", "-v" ], capture_output=True, text=True )
        print( result.stdout )
        result = subprocess.run( [ "ls", "-la", alice_local ], capture_output=True, text=True )
        print( result.stdout )
        result = subprocess.run( [ "ls", "-la", bob_local ], capture_output=True, text=True )
        print( result.stdout )

        # You can use this directory for temporary file storage
        temp_file_path = os.path.join(temp_dir, 'temp_file.txt')
        with open(temp_file_path, 'w') as temp_file:
            temp_file.write('This is a temporary file.')

        # The temporary directory and its contents are automatically deleted
        # when the context manager exits

    # At this point, the temporary directory and its contents have been deleted
    print(f'Temporary directory exists after with block: {os.path.exists(temp_dir)}')
    return 0

if __name__ == "__main__":
    import argparse
    sys.exit( main() )
