# CornCob

import os
import sys
import subprocess
import secrets
import yaml
import pathlib
import shutil
import tempfile

program_title = "CornCob protocol Git remote helper work-a-like"

class Corncob:

    def __init__( self, remote_name ):
        self.remote_name = remote_name
        self.url = None

    def main( self, cmd, dotdotdot ):
        if cmd == "clone":
            if len( dotdotdot ) < 1:
                print( f"ERROR: clone requires a URL ({program_title})" )
                return -1
            return self.clone_from_remote( dotdotdot[ 0 ] )

        result = self.change_to_root_git_dir()
        if result != 0:
            return result

        print( f"Hello World! {cmd} {self.remote_name} {dotdotdot}" )

        if cmd == "add":
            if len( dotdotdot ) < 1:
                print( f"ERROR: remote-add requires a URL ({program_title})" )
                return -1
            return self.add_remote( dotdotdot[ 0 ], dotdotdot[ 1: ] )
        elif cmd == "remove":
            return self.remove_remote( dotdotdot )

        
        self.initialize_existing_remote()
        if self.url == None:
            return -1

        self.remote = CornCobRemote.init( self.url )

        if cmd == "push":
            return self.push_to_remote( dotdotdot )
        elif cmd == "fetch":
            return self.fetch_from_remote( dotdotdot )
        elif cmd == "merge":
            return self.merge_from_remote( dotdotdot )
        else:
            print( f"ERROR: Unknown command '{cmd}' ({program_title})" )


    def add_remote( self, url, dotdotdot ):
        """Add a CornCob remote

        :param remote: The nickname for the remote
        :param url: The URL for the remote. (This should not include 'corncob:')

        Currently the only supported URL schema is file://
        In the fullness of time the idea is to support googledrive: , etc

        This function adds 2 remotes to the underlying repo:
        - One with the actual remote URL
          - This one is never directly `git fetch`d or `git push`d or whatever
        - One with a temp bundle name
          - When pulling from a remote, the bundle is copied here and `git fetch`d
        """

        git_cmd = [ "git", "remote", "add", self.remote_name, f"corncob:{url}" ]
        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
        if result.returncode == 0:
            print( f"Added remote '{self.remote_name}' ({url})" )
        else:
            print( f"ERROR: Failed to add remote '{self.remote_name}' url: '{url}' {result.stderr} ({program_title})" )
            return -1

        [ bundle_remote, path ] = self.bundle_tmp()
        git_cmd = [ "git", "remote", "add", bundle_remote, f"{path}/fetch.bundle" ]

        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
        if result.returncode == 0:
            print( f"Added remote '{bundle_remote}' ({path})" )
        else:
            print( f"ERROR: Failed to add remote '{bundle_remote}' url: '{path}' {result.stderr} ({program_title})" )
            return -1

        return 0


    def remove_remote( self, dotdotdot ):
        """Remove a CornCob remote
        """

        git_cmd = [ "git", "remote", "remove", self.remote_name ]
        result1 = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
        if result1.returncode == 0:
            print( f"Removed remote '{self.remote_name}'" )
        else:
            print( f"ERROR: Failed to remove remote '{self.remote_name}' {result1.stderr} ({program_title})" )

        [ bundle_remote, _ ] = self.bundle_tmp()
        git_cmd = [ "git", "remote", "remove", bundle_remote ]
        result2 = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
        if result2.returncode == 0:
            print( f"Removed remote '{bundle_remote}'" )
        else:
            print( f"ERROR: Failed to remove remote '{bundle_remote}' {result2.stderr} ({program_title})" )

        if result1.returncode == 0 and result2.returncode == 0:
            return 0

        return -1


    def initialize_existing_remote( self ):
        """ git remote get-url `remote_name`
        with some error checking. Plus strip the 'corncob:' prefix,
        """
        git_cmd = [ "git", "remote", "get-url", self.remote_name ]
        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )

        if result.returncode != 0:
            print( f"ERROR: Unknown remote '{self.remote_name}' {result.stderr} ({program_title})" )
            return None

        remote_url = result.stdout.strip()

        if not remote_url.startswith( "corncob:" ):
            print( f"ERROR: Wrong remote protocol '{remote_url}' ({program_title})" )
            return None

        # Strip 'corncob:'
        self.url = remote_url[ 8: ]


    def push_to_remote( self, branches ):
        print( f"PUSH {self.remote_name} {self.url} '{branches}'" )
        latest_link = self.remote.get_latest_link()

        if latest_link is None:
            bundle_uid = Corncob.token_hex( 8 )
            [ _, path_tmp ] = self.bundle_tmp()
            os.makedirs( path_tmp, exist_ok=True )
            bundle_path_tmp = f"{path_tmp}/B-{bundle_uid}.bundle"
            git_cmd = [ "git", "bundle", "create", bundle_path_tmp, "main" ]

            result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )

            if result.returncode != 0:
                print( f"git bundle failed {result.stderr}" )
                return -1

            prerequisites = { "main": "initial-snapshot" }
            blob = self.build_link_blob( "initial-snapshot", "initial-snapshot", bundle_uid, prerequisites )
            print( f"Initializing new CornCob clone '{bundle_path_tmp}' {blob}" )
            #         - - uid for this link
            #           - uid for prev link -or- "initial-snapshot"
            #           - uid for link before that, etc
            #         - *** branches ***
            #         - - - random id for latest bundle
            #             - - branch name
            #               - sha before
            #             - - branch name
            #               - sha before
            #           - - random id for prev bundle
            #             - - branch name
            #               - sha before
            #             - - branch name
            #               - sha before
            #           - - random id for bundle before that, etc
            #         - { k/v s }
                   

            #     return 0
            return self.remote.upload_latest_link( blob, bundle_uid, bundle_path_tmp )

        else:
            raise NotImplementedError( f"Updating CornCob clone. {remote_name} {corncob_url}" )


    def build_link_blob( self, new_link_uid, prev_link_uid, bundle_uid, prerequisites ):
        link_ids = [ new_link_uid, prev_link_uid ]
        branch_names = self.get_branches()
        branches = []
        for branch in branch_names:
            branches.append( [ branch, self.get_branch_head_sha( branch ) ] )
        print( f"BRANCHES {branches}" )
        bundles = [ [ bundle_uid, [ "main", prerequisites[ "main" ] ] ] ]
        supplement = {}
        return [ link_ids, branches, bundles, supplement ]


    def clone_from_remote( self, url ):
        print( f"CLONE {self.remote_name} {url}" )

        git_cmd = [ "git", "rev-parse", "--show-toplevel" ]
        result = subprocess.run( git_cmd, capture_output=True, text=True )
        if result.returncode == 0:
            print( f"ERROR. Trying to clone, but already in a repo '{os.getcwd()}' '{result.stdout.strip()}' ({program_title})" )
            return -1

        # git_cmd = [ "git", "init" ]
        # result = subprocess.run( git_cmd, capture_output=True, text=True )
        # if result.returncode != 0:
        #     print( f"ERROR. clone > git init failed. ({program_title})" )
        #     return result.returncode
        # result = self.add_remote( url, [] ):
        
        self.remote = CornCobRemote.init( url )
        latest_link = self.remote.get_latest_link()
        if latest_link == None:
            print( f"CLONE SADNESS" )
            return -1
        
        [ link_ids, branches, bundles, supp_data ] = latest_link
        if link_ids[ 0 ] != "initial-snapshot":
            print( f"CLONE MORE THAN INIT {link_ids[ 0 ]}" )
            return -1

        if len( bundles ) != 1:
            print( f"CLONE BS {bundles}" )
            return -1

        bundle = bundles[ 0 ]
        bundle_uid = bundle[ 0 ]

        with tempfile.TemporaryDirectory() as bundle_temp_dir:
            bundle_path = f"{bundle_temp_dir}/clone.bundle"
            self.remote.download_bundle( bundle_uid, bundle_path )

            git_cmd = [ "git", "clone", bundle_path, "." ]
            result = subprocess.run( git_cmd, capture_output=True, text=True )
            if result.returncode != 0:
                print( f"ERROR. git clone from bundle failed {result.stdout}  {result.stderr} ({program_title})" )
                return -1

        git_cmd = [ "git", "checkout", "main" ]
        result = subprocess.run( git_cmd, capture_output=True, text=True )
        if result.returncode != 0:
            print( f"ERROR. git checkout bundle failed {result.stdout}  {result.stderr} ({program_title})" )
            return -1

        result = self.add_remote( url, [] )
        if 0 != result:
            print( f"ADD REMOTE AFTER CLONE FAILED" )
            return result
        print( f"CLONE WORKED!!!" )
        return 0
        

    def fetch_from_remote( self, branches ):
        print( f"FETCH {self.remote_name} {self.url} {branches}" )
        latest_link = self.remote.get_latest_link()

        if latest_link == None:
            print( f"ERROR: Failed to fetch latest link '{corncob_url}' ({program_title})" )
            return -1

        [ link_ids, branches, bundles, supp_data ] = latest_link
        if link_ids[ 0 ] != "initial-snapshot":
            print( f"CLONE MORE THAN INIT {link_ids[ 0 ]}" )
            return -1

        if len( bundles ) != 1:
            print( f"CLONE BS {bundles}" )
            return -1

        bundle = bundles[ 0 ]
        bundle_uid = bundle[ 0 ]

        [ tmp_remote, path_tmp ] = self.bundle_tmp()
        os.makedirs( path_tmp, exist_ok=True )

        bundle_path = f"{path_tmp}/fetch.bundle"
        self.remote.download_bundle( bundle_uid, bundle_path )

        git_cmd = [ "git", "bundle", "verify", bundle_path ]
        result = subprocess.run( git_cmd, capture_output=True, text=True )
        if result.returncode != 0:
            print( f"ERROR. git bundle verify failed {result.stdout}  {result.stderr} ({program_title})" )
            return -1

        git_cmd = [ "git", "fetch", tmp_remote ]
        result = subprocess.run( git_cmd, capture_output=True, text=True )
        if result.returncode != 0:
            print( f"ERROR. git fetch bundle failed {result.stdout}  {result.stderr} ({program_title})" )
            return -1

        git_cmd = [ "git", "branch", "-v", "-a" ]
        result = subprocess.run( git_cmd, capture_output=True, text=True )
        print( f"** git branch '{result.stdout}'  '{result.stderr}'" )

        # copy to temp location
        # git fetch remote-temp
        return 0


    def merge_from_remote( self, branches ):
        print( f"MERGE {self.remote_name} {branches}" )
        branch = branches[ 0 ]

        [ tmp_remote, _ ] = self.bundle_tmp()

        git_cmd = [ "git", "merge", f"{tmp_remote}/{branch}" ]
        result = subprocess.run( git_cmd, capture_output=True, text=True )
        if result.returncode != 0:
            print( f"ERROR. git merge bundle failed {result.stdout}  {result.stderr} ({program_title})" )
            return -1
        return 0


    def get_branches( self ):
        """ git for-each-ref --format=%(refname:short) refs/heads/
        with error checking
        """
        git_cmd = [ "git", "for-each-ref", "--format=%(refname:short)", "refs/heads/" ]
        # cwd=repo_path, 
        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )

        if result.returncode == 0:
            return result.stdout.splitlines()

        print( "Error:", result.stderr )
        return []


    def get_branch_head_sha( self, branch ):
        command = [ "git", "rev-parse", f"refs/heads/{branch}" ]
        # cwd=repo_path,
        print( f"MLERP {branch}" )
        result = subprocess.run( command, shell=False, capture_output=True, text=True )

        if result.returncode == 0:
            return result.stdout.strip()

        print( "Error:", result.stderr )
        return "0xdeadbeef"


    def token_hex( num_bytes ):
        return "".join( f"{b:02x}" for b in secrets.token_bytes( num_bytes ) )


    def change_to_root_git_dir( self ):
        """ cd $( git rev-parse --show-toplevel )
        with some error checking
        """
        git_cmd = [ "git", "rev-parse", "--show-toplevel" ]
        result = subprocess.run( git_cmd, capture_output=True, text=True )
        if result.returncode != 0:
            print( f"ERROR. Current directory not a Git repo '{os.getcwd()}' ({program_title})" )
            return result.returncode
        git_dir = result.stdout.strip()
        os.chdir( git_dir )
        if pathlib.Path( git_dir ).resolve() == pathlib.Path( os.getcwd() ).resolve():
            return 0
        print( f"ERROR. Weird os.chdir() failure? {result.stdout} {os.getcwd()} ({program_title})" )
        return -1

    def bundle_tmp( self ):
        return [ f"{self.remote_name}-corncob-bundle-tmp",
                 f"./.corncob-bundle-tmp/{self.remote_name}" ]



class CornCobRemote:
    """ Abstract class for different kinds of remotes (Google Drive, etc)
    """
    @staticmethod
    def init( url ):
        if url.startswith( "file://" ):
            return LocalFolderRemote( url[ 7: ].strip() )

        raise NotImplementedError( f"Unsupported CornCob cloud protocol. '{corncob_url}'" )

    def read_link_blob( self, yaml_strm ):
        parsed_data = yaml.load( yaml_strm, Loader=yaml.FullLoader )
        link_ids = parsed_data[ 0 ]
        branches = parsed_data[ 1 ]
        bundles = parsed_data[ 2 ]
        if len( parsed_data ) > 3:
            supp_data = parsed_data[ 3 ]
        else:
            supp_data = {}
        return [ link_ids, branches, bundles, supp_data ]


class LocalFolderRemote( CornCobRemote ):
    """ Mostly for debugging purposes. Pretend a local folder is a cloud location.
    """

    def __init__( self, path ):
        self.path = None

        if not os.path.isdir( path ):
            print( f"ERROR: File URL not a folder '{path}' ({program_title})" )
            return -1

        self.path = path


    def upload_latest_link( self, blob, bundle_uid, local_bundle_path ):
        path_bundle = f"{self.path}{os.path.sep}B-{bundle_uid}.bundle"
        # TODO: error handling
        shutil.copy( local_bundle_path, path_bundle )

        path_latest = f"{self.path}{os.path.sep}latest-link.yaml"
        with open( path_latest, "w", encoding="utf-8" ) as link_strm:
            yaml.dump( blob, link_strm, default_flow_style=False )


    def get_latest_link( self ):
        path_latest = f"{self.path}{os.path.sep}latest-link.yaml"

        if not os.path.exists( path_latest ):
            return None

        with open( path_latest, "r" ) as link_file_strm:
            return self.read_link_blob( link_file_strm )


    def download_bundle( self, bundle_uid, local_bundle_path ):
        path_bundle = f"{self.path}{os.path.sep}B-{bundle_uid}.bundle"
        # TODO: error handling
        shutil.copy( path_bundle, local_bundle_path )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser( program_title )
    parser.add_argument( "command", type=str )
    parser.add_argument( "remote", type=str )
    parser.add_argument( "branches", nargs=argparse.REMAINDER )

    args = parser.parse_args()

    corncob = Corncob( args.remote )
    sys.exit( corncob.main( args.command, args.branches ) )
