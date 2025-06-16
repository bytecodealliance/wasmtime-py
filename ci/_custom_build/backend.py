"""
An in-tree PEP-517 build backend that downloads wasmtime and generates Python
bindings. It extends the PEP-517 backend provided by setuptools.

See
- https://peps.python.org/pep-0517/#build-backend-interface
- https://setuptools.pypa.io/en/latest/build_meta.html#dynamic-build-dependencies-and-other-build-meta-tweaks
"""

import subprocess
import sys

from typing import Union

# `from ... import *` is intentional and necessary, so that any PEP-517 hooks
# not overridden here are still available to build frontends.
from setuptools import build_meta as build_meta_orig
from setuptools.build_meta import *


def get_plat_name(config_settings:Union[dict, None]) -> Union[str, None]:
    """
    Return the value of any --plat-name passed to the build frontend,
    otherwise None.

    >>> get_plat_name({'--build-option': ['--plat-name', 'manylinux1-x86_64']})
    'manylinux1-x86_64'
    >>> print(get_plat_name(None))
    None
    >>> print(get_plat_name({}))
    None
    >>> print(get_plat_name({'--build-option': []}))
    None
    """
    if config_settings is None:
        return None

    try:
        build_options = config_settings['--build-option']
    except KeyError:
        return None

    try:
        plat_name_option_idx = build_options.index('--plat-name')
    except ValueError:
        return None

    plat_name = build_options[plat_name_option_idx+1]
    return plat_name


def plat_name_to_download_args(plat_name:str) -> list[str]:
    "Return a list of download-wasmtime.py arguments for a given platform name."
    mapping = {
        'android_26_arm64_v8a':         ['android', 'aarch64'],
        'android_26_x86_64':            ['android', 'x86_64'],
        'macosx-10-13-x86_64':          ['darwin', 'x86_64'],
        'macosx-11-0-arm64':            ['darwin', 'arm64'],
        'manylinux1-x86_64':            ['linux', 'x86_64'],
        'manylinux2014_aarch64':        ['linux', 'aarch64'],
        'musllinux_1_2_x86_64':         ['musl', 'x86_64'],
        'win-amd64':                    ['win32', 'x86_64'],
        'win-arm64':                    ['win32', 'arm64'],
    }
    return mapping[plat_name]


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    """
    Download a pre-compiled build of wasmtime and generate bindings, both to be
    included in the output Python wheel.

    This is a PEP-517 build backend function.
    """
    plat_name = get_plat_name(config_settings)
    if plat_name is not None:
        download_args = plat_name_to_download_args(plat_name)
    elif config_settings is not None and '--wasmtime-py-mingw-any' in config_settings:
        download_args = ['win32', 'x86_64']
    else:
        download_args = []

    subprocess.run(
        [sys.executable, 'ci/download-wasmtime.py', *download_args],
        check=True,
    )
    subprocess.run(
        [sys.executable, 'ci/build-rust.py'],
        check=True,
    )

    return build_meta_orig.build_wheel(wheel_directory, config_settings, metadata_directory)
