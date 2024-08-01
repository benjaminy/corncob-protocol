import tempfile
import os
import sys
import subprocess
import random
from corncob_test_utils import CorncobTest, gitCmd

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

        gitCmd( [ "init" ] )

        with open( "hi_bob.txt", "w" ) as file:
            file.write( "Hi there Bob!" )
        with open( "big.txt", "w" ) as file:
            for _ in range( 10000 ):
                file.write( random.choice( [ "Alice", "Bob", "Carol", "Dave", "Eve" ] ) )

        gitCmd( [ "add", "hi_bob.txt" ] )
        gitCmd( [ "add", "big.txt" ] )
        gitCmd( [ "commit", "-m", "greeting" ] )
        print( f"ALICE STATUS:" )
        gitCmd( [ "status", "-v" ], False )

        test_utils.corncob_cmd( [ "add", "a_team_alice", f"file://{alice_remote}" ] )
        test_utils.corncob_cmd( [ "add", "a_team_bob", f"file://{bob_remote}" ] )
        test_utils.corncob_cmd( [ "push", "a_team_alice" ] )

        result = subprocess.run( [ "ls", alice_remote ], capture_output=True, text=True )
        print( result.stdout )

        os.chdir( bob_local )

        test_utils.corncob_cmd( [ "clone", "a_team_alice", f"file://{alice_remote}" ] )

        result = subprocess.run( [ "git", "status", "-v" ], capture_output=True, text=True )
        print( result.stdout )
        result = subprocess.run( [ "ls", "-la", alice_local ], capture_output=True, text=True )
        print( result.stdout )
        result = subprocess.run( [ "ls", "-la", bob_local ], capture_output=True, text=True )
        print( result.stdout )

        test_utils.corncob_cmd( [ "add", "a_team_bob", f"file://{bob_remote}" ] )

        with open( "hi_bob.txt", "a" ) as file:
            file.write( "Hello Alice!" )

        gitCmd( [ "add", "hi_bob.txt" ] )
        gitCmd( [ "commit", "-m", "back at you" ] )
        test_utils.corncob_cmd( [ "push", "a_team_bob" ] )

        result = subprocess.run( [ "ls", bob_remote ], capture_output=True, text=True )
        print( result.stdout )

        os.chdir( alice_local )

        test_utils.corncob_cmd( [ "fetch", "a_team_bob" ] )
        test_utils.corncob_cmd( [ "merge", "a_team_bob", "main" ] )

        with open( "hi_bob.txt", "r" ) as file:
            print( file.read() )

        with open( "hi_bob.txt", "a" ) as file:
            file.write( " How about dinner?" )
        gitCmd( [ "add", "hi_bob.txt" ] )
        gitCmd( [ "commit", "-m", "a proposal" ] )
        test_utils.corncob_cmd( [ "push", "a_team_alice" ] )

        print( "Alice's remote dir:" )
        result = subprocess.run( [ "ls", "-l", alice_remote ], capture_output=True, text=True )
        print( result.stdout )

        os.chdir( bob_local )

        test_utils.corncob_cmd( [ "fetch", "a_team_alice" ] )
        test_utils.corncob_cmd( [ "merge", "a_team_alice", "main" ] )

        with open( "hi_bob.txt", "r" ) as file:
            print( file.read() )
    return 0

if __name__ == "__main__":
    import argparse
    sys.exit( main() )
