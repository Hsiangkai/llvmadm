"""Simple script to manage the LLVM monorepo (llvm-project)."""

import argparse, shutil, os, multiprocessing
import subprocess

llvm_source = os.path.dirname(os.path.abspath(__file__))

DEFAULT_PROJECTS = 'clang;lld;mlir'
DEFAULT_RUNTIMES = 'compiler-rt;libcxx;libcxxabi;libunwind'


def update():
    os.chdir(llvm_source)
    subprocess.call('git pull --rebase', shell=True)


def checkout(branch):
    os.chdir(llvm_source)
    subprocess.call('git checkout {}'.format(branch), shell=True)


def build(prefix, buildpath, targets, build_type, projects, runtimes, clean, jobs, no_install):
    build_dir = os.path.join(llvm_source, buildpath)
    need_cmake = False

    if clean and os.path.isdir(build_dir):
        shutil.rmtree(build_dir)

    if not os.path.isdir(build_dir):
        os.makedirs(build_dir)
        need_cmake = True
    elif not os.path.exists(os.path.join(build_dir, 'build.ninja')) and \
         not os.path.exists(os.path.join(build_dir, 'Makefile')):
        need_cmake = True

    if need_cmake:
        cmake_args = [
            'cmake',
            '-S', os.path.join(llvm_source, 'llvm'),
            '-B', build_dir,
            '-DCMAKE_BUILD_TYPE={}'.format(build_type),
            '-DCMAKE_INSTALL_PREFIX={}'.format(prefix),
            '-DLLVM_TARGETS_TO_BUILD={}'.format(targets),
        ]
        if projects:
            cmake_args += ['-DLLVM_ENABLE_PROJECTS={}'.format(projects)]
        if runtimes:
            cmake_args += ['-DLLVM_ENABLE_RUNTIMES={}'.format(runtimes)]

        if shutil.which('ninja'):
            cmake_args += ['-G', 'Ninja']

        subprocess.call(cmake_args)

    use_ninja = shutil.which('ninja') and os.path.exists(os.path.join(build_dir, 'build.ninja'))

    if use_ninja:
        subprocess.call(['ninja', '-C', build_dir, '-j', str(jobs)])
        if not no_install:
            subprocess.call(['ninja', '-C', build_dir, 'install'])
    else:
        subprocess.call(['make', '-C', build_dir, '-j', str(jobs)])
        if not no_install:
            subprocess.call(['make', '-C', build_dir, 'install'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage the LLVM monorepo')
    sub_parsers = parser.add_subparsers(dest='command', metavar='command')
    sub_parsers.required = True

    sub_parsers.add_parser('update', help='update llvm-project via git pull --rebase')

    sub_parser = sub_parsers.add_parser('checkout', help='switch to a branch')
    sub_parser.add_argument('-b', '--branch', required=True)

    sub_parser = sub_parsers.add_parser('build', help='configure and build LLVM')
    sub_parser.add_argument('--prefix', default=os.path.expanduser('~/llvm-dev'),
                            help='installation prefix (default: ~/llvm-dev)')
    sub_parser.add_argument('--buildpath', default='build',
                            help='build directory relative to repo root (default: build)')
    sub_parser.add_argument('--targets', default='host',
                            help='LLVM_TARGETS_TO_BUILD (default: host)')
    sub_parser.add_argument('--projects', default=DEFAULT_PROJECTS,
                            help='semicolon-separated LLVM_ENABLE_PROJECTS '
                                 '(default: {})'.format(DEFAULT_PROJECTS))
    sub_parser.add_argument('--runtimes', default=DEFAULT_RUNTIMES,
                            help='semicolon-separated LLVM_ENABLE_RUNTIMES '
                                 '(default: {})'.format(DEFAULT_RUNTIMES))
    sub_parser.add_argument('--debug', action='store_true',
                            help='use Debug build type (default: Release)')
    sub_parser.add_argument('--clean', action='store_true',
                            help='wipe the build directory before building')
    sub_parser.add_argument('--no-install', action='store_true',
                            help='skip the install step')
    sub_parser.add_argument('-j', '--jobs', type=int,
                            default=multiprocessing.cpu_count(),
                            help='parallel jobs (default: cpu count)')

    args = parser.parse_args()

    if args.command == 'update':
        update()
    elif args.command == 'checkout':
        checkout(args.branch)
    elif args.command == 'build':
        build_type = 'Debug' if args.debug else 'Release'
        build(args.prefix, args.buildpath, args.targets, build_type,
              args.projects, args.runtimes, args.clean, args.jobs, args.no_install)
    else:
        assert False, 'unexpected command {!r}'.format(args.command)
