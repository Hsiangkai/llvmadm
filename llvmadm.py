"""Simple script to manage LLVM source tree.

"""

import argparse, shutil, os
import subprocess

tools = ['clang', 'lldb', 'lld']
projects = ['compiler-rt', 'test-suite']
llvm_source=os.getcwd()
cmake_command = 'cmake -DCMAKE_INSTALL_PREFIX={} -DCMAKE_BUILD_TYPE={} -G "Unix Makefiles" {}'

llvm_repo = {'clang': 'https://github.com/llvm-mirror/clang.git',
        'lldb': 'https://github.com/llvm-mirror/lldb.git',
        'lld': 'https://github.com/llvm-mirror/lld.git',
        'compiler-rt': 'https://github.com/llvm-mirror/compiler-rt.git',
        'test-suite': 'https://github.com/llvm-mirror/test-suite.git'
        }

def is_lbranch_exist(branch):
    if branch == 'master':
        return True

    proc = subprocess.Popen("git branch",
            stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    branches = proc.communicate()[0]
    for lbranch in branches.splitlines():
        if lbranch[2:] == branch:
            return True

    return False

def available_rbranch():
    proc = subprocess.Popen("git branch -a",
            stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    branches = proc.communicate()[0]

    avail_branch = []
    for rbranch in branches.splitlines():
        if 'origin' in rbranch:
            branch_pos = rbranch.rfind('/')
            # skip 'master' branch
            if rbranch[branch_pos+1:] == 'master':
                continue
            avail_branch.append(rbranch[branch_pos+1:])

    return avail_branch


def create_lbranch(branch):
    branches = available_rbranch()
    if not branch in branches:
        return False

    subprocess.call("git checkout -b {} origin/{}".format(branch, branch),
            shell=True)
    return True

def checkout_lbranch(branch):
    subprocess.call("git checkout {}".format(branch), shell=True)

def clone_project(project):
    subprocess.call("git clone {}".format(llvm_repo[project]), shell=True)
    return

def checkout(branch):
    os.chdir(llvm_source)
    if not is_lbranch_exist(branch):
        create_lbranch(branch)
    else:
        checkout_lbranch(branch)

    for tool in tools:
        tool_dir = os.path.join(llvm_source, 'tools', tool)
        if not os.path.isdir(tool_dir):
            os.chdir(os.path.join(llvm_source, 'tools'))
            clone_project(tool)

        os.chdir(tool_dir)
        if not is_lbranch_exist(branch):
            create_lbranch(branch)
        else:
            checkout_lbranch(branch)

    for project in projects:
        project_dir = os.path.join(llvm_source, 'projects', project)
        if not os.path.isdir(project_dir):
            os.chdir(os.path.join(llvm_source, 'projects'))
            clone_project(project)

        os.chdir(project_dir)
        if not is_lbranch_exist(branch):
            create_lbranch(branch)
        else:
            checkout_lbranch(branch)

def update():
    # update LLVM source first
    os.chdir(llvm_source)
    subprocess.call("git pull --rebase", shell=True)

    # update tools subtree
    for tool in tools:
        tool_dir = os.path.join(llvm_source, "tools", tool)
        if os.path.isdir(tool_dir):
            os.chdir(tool_dir)
            subprocess.call("git pull --rebase", shell=True)

    # update projects subtree
    for project in projects:
        project_dir = os.path.join(llvm_source, "projects", project)
        if os.path.isdir(project_dir):
            os.chdir(project_dir)
            subprocess.call("git pull --rebase", shell=True)

    return

def build(prefix, debug, clean):
    build_dir = os.path.join(llvm_source, 'build')
    build_dir_empty = False

    if clean:
        shutil.rmtree(build_dir, ignore_errors=True)
        os.mkdir(build_dir)
        build_dir_empty = True

    if os.path.isdir(build_dir) == False:
        os.mkdir(build_dir)
        build_dir_empty = True

    # The possible values include Debug, Release, RelWithDebInfo,
    # and MinSizeRel. Only support Release and Debug now.
    build_type = 'Release'
    if debug:
        build_type = 'Debug'

    os.chdir(build_dir)
    if build_dir_empty:
        subprocess.call(cmake_command.format(prefix, build_type, llvm_source), shell=True)

    subprocess.call("make -j4", shell=True)
    subprocess.call("make install", shell=True)

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub_parsers = parser.add_subparsers(dest='command', metavar='command')
    sub_parsers.required = True

    sub_parser = sub_parsers.add_parser('update',
            help='update LLVM from GitHub')

    sub_parser = sub_parsers.add_parser('checkout',
            help='switch LLVM branch')
    sub_parser.add_argument('-b', '--branch', required=True)

    sub_parser = sub_parsers.add_parser('build',
            help='build LLVM')
    sub_parser.add_argument('--prefix', default='$HOME/llvm-dev')
    sub_parser.add_argument('--debug', action='store_true')
    sub_parser.add_argument('--clean', action='store_true')

    args = parser.parse_args()
    if args.command == 'update':
        update()
    elif args.command == 'checkout':
        checkout(args.branch)
    elif args.command == 'build':
        build(args.prefix, args.debug, args.clean)
    else:
        assert False, 'unexpected command {!r}'.format(args.command)
