# CornCob

import os
import subprocess
import secrets
import yaml
import pathlib
import shutil

program_title = "CornCob protocol Git remote helper work-a-like"

def main( cmd, remote, dotdotdot ):
    result = change_to_root_git_dir()
    if result != 0:
        return result

    print( f"Hello World! {cmd} {remote} {dotdotdot}" )

    if cmd == "add":
        return corncob_add( remote, dotdotdot[ 0 ], dotdotdot[ 1: ] )
    elif cmd == "remove":
        return corncob_remove( remote, dotdotdot )

    corncob_url = get_corncob_url( remote )
    if corncob_url == None:
        return -1

    if cmd == "push":
        return corncob_push( remote, corncob_url, dotdotdot )
    elif cmd == "fetch":
        return corncob_fetch( remote, corncob_url, dotdotdot )
    elif cmd == "clone":
        return corncob_clone( remote, corncob_url, dotdotdot )
    else:
        print( f"{program_title}: error: Unknown command '{cmd}'" )


def corncob_add( remote, url, dotdotdot ):
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

    git_cmd = [ "git", "remote", "add", remote, f"corncob:{url}" ]
    result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
    if result.returncode != 0:
        print( f"{program_title}: error: Failed to add remote '{remote}' url: '{url}' {result.stderr}" )
        return -1

    bundle_remote = f"{remote}-corncob-bundle-tmp"
    path = f"./.corncob-bundle-tmp/{remote}.bundle"
    git_cmd = [ "git", "remote", "add", bundle_remote, path ]

    result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
    if result.returncode != 0:
        print( f"{program_title}: error: Failed to add remote '{bundle_remote}' url: '{path}' {result.stderr}" )
        return -1

    return 0


def corncob_remove( remote, dotdotdot ):
    """Remove a CornCob remote
    """

    git_cmd = [ "git", "remote", "remove", remote ]
    result1 = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
    if result1.returncode != 0:
        print( f"{program_title}: error: Failed to remove remote '{remote}' {result1.stderr}" )

    bundle_remote = f"{remote}-corncob-bundle-tmp"
    git_cmd = [ "git", "remote", "remove", bundle_remote ]
    result2 = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
    if result2.returncode != 0:
        print( f"{program_title}: error: Failed to remove remote '{bundle_remote}' {result2.stderr}" )

    if result1.returncode == 0 && result2.returncode == 0:
        return 0

    return -1


def corncob_push( remote_name, corncob_url, branches ):
    print( f"PUSH {remote_name} {corncob_url} {branches}" )
    remote = CornCobRemote.init( corncob_url )
    latest_link = remote.get_latest_link()

    if latest_link is None:
        bundle_uid = token_hex( 8 )
        local_bundle_path = f".{os.path.sep}.corncob-bundle-tmp{os.path.sep}tmp-{bundle_uid}.bundle"
        git_cmd = [ "git", "bundle", "create", local_bundle_path, "main" ]

        result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )

        if result.returncode != 0:
            print( f"git bundle failed {result.stderr}" )
            return -1

        prerequisites = { "main", "initial-snapshot" }
        blob = build_link_blob( "initial-snapshot", "initial-snapshot", bundle_uid, prerequisites )
        print( f"Initializing new CornCob clone '{path_str}' {blob}" )
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
        return remote.upload_latest_link( blob, bundle_uid, local_bundle_path )

    else:
        raise NotImplementedError( f"Updating CornCob clone. {remote_name} {corncob_url}" )



def build_link_blob( new_link_uid, prev_link_id, bundle_uid, prerequisites ):
    link_ids = [ new_link_uid, prev_link_uid ]
    branch_names = get_branches()
    branches = []
    for branch in branch_names:
        branches.append( [ branch, get_branch_head_sha( branch ) ] )
    print( f"BRANCHES {branches}" )
    bundles = [ [ bundle_uid, [ "main", prerequisites[ "main" ] ] ] ]
    supplement = {}
    return [ link_ids, branches, bundles, supplement ]


def corncob_fetch( remote, corncob_url, branches ):
    print( f"FETCH {remote} {corncob_url} {branches}" )
    remote = CornCobRemote.init( corncob_url )
    latest_link = remote.get_latest_link()

    if latest_link == None:
        print( f"ERROR: Failed to fetch latest link '{corncob_url}' ({program_title})" )
        return -1


    path_tmp = f".{os.path.sep}.corncob-bundle-tmp{os.path.sep}{remote}.bundle"

    # copy to temp location
    # git fetch remote-temp


def get_branches():
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


def get_branch_head_sha( branch ):
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


def change_to_root_git_dir():
    """ cd $( git rev-parse --show-toplevel )
    with some error checking
    """
    git_cmd = [ "git" "rev-parse" "--show-toplevel" ]
    result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )
    if result.returncode != 0:
        print( f"ERROR. Current directory not a Git repo '{os.getcwd()}' ({program_title})" )
        return result.returncode
    os.chdir( result.stdout )
    if pathlib.Path( result.stdout ).resolve() == pathlib.Path( os.getcwd() ).resolve():
        return 0
    print( f"ERROR. Weird os.chdir() failure? {result.stdout} {os.getcwd()} ({program_title})" )
    return -1


def get_corncob_url( remote_name ):
    """ git remote get-url `remote_name`
    with some error checking. Plus strip the 'corncob:' prefix,
    """
    git_cmd = [ "git", "remote", "get-url", remote_name ]
    result = subprocess.run( git_cmd, shell=False, capture_output=True, text=True )

    if result.returncode != 0:
        print( f"ERROR: Unknown remote '{remote_name}' {result.stderr} ({program_title})" )
        return None

    remote_url = result.stdout

    if not remote_url.startswith( "corncob:" ):
        print( f"ERROR: Wrong remote protocol '{remote_url}' ({program_title})" )
        return None

    # Strip 'corncob:'
    return remote_url[ 8: ]


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
        if len( parsed_data > 3 ):
            supp_data = parsed_data[ 3 ]
        else:
            supp_data = {}


class LocalFolderRemote( CornCobRemote ):
    """ Mostly for debugging purposes. Pretend a local folder is a cloud location.
    """

    def __init__( self, path ):
        self.path = None

        if not os.path.isdir( path ):
            print( f"ERROR: File URL not a folder '{path}' ({program_title})" )
            return -1

        self.path = path


    def upload_latest_link( blob, bundle_uid, local_bundle_path ):
        path_latest = f"{self.path}{os.path.sep}latest-link.yaml"
        with open( path_latest, "w", encoding="utf-8" ) as link_strm:
            yaml.dump( blob, link_strm, default_flow_style=False )

        path_bundle = f"{self.path}{os.path.sep}B{bundle_uid}.bundle"
        # TODO: error handling
        shutil.copy( local_bundle_path, path_bundle )


    def get_latest_link():
        path_latest = f"{self.path}{os.path.sep}latest-link.yaml"

        if not os.path.exists( path_latest ):
            return None

        with open( path_latest, "r" ) as link_file_strm:
            return read_link_blob( link_file_strm )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser( program_title )
    parser.add_argument( "command", type=str )
    parser.add_argument( "remote", type=str )
    parser.add_argument( "branches", nargs=argparse.REMAINDER )

    args = parser.parse_args()

    exit_code = main( args.command, args.remote, args.branches )
