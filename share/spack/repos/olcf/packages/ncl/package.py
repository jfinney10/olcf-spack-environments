# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *
import glob
import os
import tempfile


class Ncl(Package):
    """NCL is an interpreted language designed specifically for
       scientific data analysis and visualization. Supports NetCDF 3/4,
       GRIB 1/2, HDF 4/5, HDF-EOD 2/5, shapefile, ASCII, binary.
       Numerous analysis functions are built-in."""

    homepage = "https://www.ncl.ucar.edu"

    url = "https://github.com/NCAR/ncl/archive/6.4.0.tar.gz"

    version('6.5.0', '133446f3302eddf237db56bf349e1ebf228240a7320699acc339a3d7ee414591')
    version('6.4.0', 'd891452cda7bb25afad9b6c876c73986')
    version('6.3.0', 'd2cd8a1de1c498c1832f0765113ad58086d1d3b29bf5d2cc9b1ba60f1919951c')

    patch('configure_v6.5.0.patch', when="@6.5.0")
    patch('configure_v6.4.0.patch', when="@:6.4.0")
    # Make ncl compile with hdf5 1.10 (upstream as of 6.5.0)
    patch('hdf5.patch', when="@6.4.0")
    # ymake-filter's buffer may overflow (upstream as of 6.5.0)
    patch('ymake-filter.patch', when="@6.4.0")

    # This installation script is implemented according to this manual:
    # http://www.ncl.ucar.edu/Download/build_from_src.shtml

    variant('hdf4', default=False, description='Enable HDF4 support.')
    variant('gdal', default=False, description='Enable GDAL support.')
    variant('triangle', default=True, description='Enable Triangle support.')
    variant('udunits2', default=True, description='Enable UDUNITS-2 support.')
    variant('openmp', default=True, description='Enable OpenMP support.')

    # Non-optional dependencies according to the manual:
    depends_on('jpeg')
    depends_on('netcdf~mpi~parallel-netcdf')
    depends_on('cairo+X+pdf')

    # Extra dependencies that may be missing from build system:
    depends_on('bison', type='build')
    depends_on('flex+lex')
    depends_on('libiconv')
    depends_on('tcsh')

    # Also, the manual says that ncl requires zlib, but that comes as a
    # mandatory dependency of libpng, which is a mandatory dependency of cairo.

    # The following dependencies are required, otherwise several components
    # fail to compile:
    depends_on('curl')
    depends_on('libiconv')
    depends_on('libx11')
    depends_on('libxaw')
    depends_on('libxmu')

    # In Spack, we do not have an option to compile netcdf without netcdf-4
    # support, so we will tell the ncl configuration script that we want
    # support for netcdf-4, but the script assumes that hdf5 is compiled with
    # szip support. We introduce this restriction with the following dependency
    # statement.
    depends_on('hdf5+szip~mpi')
    depends_on('szip')

    # ESMF is only required at runtime (for ESMF_regridding.ncl)
    depends_on('esmf~mpi~pnetcdf', type='run')

    # In Spack, we also do not have an option to compile netcdf without DAP
    # support, so we will tell the ncl configuration script that we have it.

    # Some of the optional dependencies according to the manual:
    depends_on('hdf', when='+hdf4')
    depends_on('netcdf+hdf4', when='+hdf4')
    depends_on('gdal', when='+gdal')
    depends_on('udunits2', when='+udunits2')

    # We need src files of triangle to appear in ncl's src tree if we want
    # triangle's features.
    resource(
        name='triangle',
        url='http://www.netlib.org/voronoi/triangle.zip',
        md5='10aff8d7950f5e0e2fb6dd2e340be2c9',
        placement='triangle_src',
        when='+triangle')

    def patch(self):
        # Make configure scripts use Spack's tcsh
        files = ['Configure'] + glob.glob('config/*')

        filter_file('^#!/bin/csh -f', '#!/usr/bin/env csh', *files)

    @run_before('install')
    def filter_sbang(self):
        # Filter sbang before install so Spack's sbang hook can fix it up
        files = glob.glob('ncarg2d/src/bin/scripts/*')
        files += glob.glob('ncarview/src/bin/scripts/*')
        files += glob.glob('ni/src/scripts/*')

        csh = join_path(self.spec['tcsh'].prefix.bin, 'csh')

        filter_file('^#!/bin/csh', '#!{0}'.format(csh), *files)

    def install(self, spec, prefix):

        if (self.compiler.fc is None) or (self.compiler.cc is None):
            raise InstallError('NCL package requires both '
                               'C and Fortran compilers.')

        self.prepare_site_config()
        self.prepare_install_config()
        self.prepare_src_tree()
        make('Everything', parallel=False)

    def setup_environment(self, spack_env, run_env):
        run_env.set('NCARG_ROOT', self.spec.prefix)

    def prepare_site_config(self):
        fc_flags = []
        cc_flags = []
        c2f_flags = []

        if '+openmp' in self.spec:
            fc_flags.append(self.compiler.openmp_flag)
            cc_flags.append(self.compiler.openmp_flag)

        if self.compiler.name == 'gcc':
            fc_flags.append('-fno-range-check')
            c2f_flags.extend(['-lgfortran', '-lm'])
        elif self.compiler.name == 'intel':
            fc_flags.append('-fp-model precise')
            cc_flags.append('-fp-model precise')
            c2f_flags.extend(['-lifcore', '-lifport'])

        with open('./config/Spack', 'w') as f:
            f.writelines([
                '#define HdfDefines\n',
                '#define CppCommand \'/usr/bin/env cpp -traditional\'\n',
                '#define CCompiler cc\n',
                '#define FCompiler fc\n',
                ('#define CtoFLibraries ' + ' '.join(c2f_flags) + '\n'
                 if len(c2f_flags) > 0
                 else ''),
                ('#define CtoFLibrariesUser ' + ' '.join(c2f_flags) + '\n'
                 if len(c2f_flags) > 0
                 else ''),
                ('#define CcOptions ' + ' '.join(cc_flags) + '\n'
                 if len(cc_flags) > 0
                 else ''),
                ('#define FcOptions ' + ' '.join(fc_flags) + '\n'
                 if len(fc_flags) > 0
                 else ''),
                '#define BuildShared NO'
            ])

    def prepare_install_config(self):
        # Remove the results of the previous configuration attempts.
        self.delete_files('./Makefile', './config/Site.local')

        # Generate an array of answers that will be passed to the interactive
        # configuration script.
        config_answers = [
            # Enter Return to continue
            '\n',
            # Build NCL?
            'y\n',
            # Parent installation directory :
            "'%s'\n" % self.spec.prefix,
            # System temp space directory:
            "'%s'\n" % tempfile.gettempdir(),
            # Build NetCDF4 feature support (optional)?
            'y\n'
        ]

        if self.spec.satisfies('+hdf4'):
            config_answers.extend([
                # Build HDF4 support (optional) into NCL?
                'y\n',
                # Also build HDF4 support (optional) into raster library?
                'y\n',
                # Did you build HDF4 with szip support?
                'y\n' if self.spec.satisfies('^hdf+szip') else 'n\n'
            ])
        else:
            config_answers.extend([
                # Build HDF4 support (optional) into NCL?
                'n\n',
                # Also build HDF4 support (optional) into raster library?
                'n\n'
            ])

        config_answers.extend([
            # Build Triangle support (optional) into NCL
            'y\n' if '+triangle' in self.spec else 'n\n',
            # If you are using NetCDF V4.x, did you enable NetCDF-4 support?
            'y\n',
            # Did you build NetCDF with OPeNDAP support?
            'y\n',
            # Build GDAL support (optional) into NCL?
            'y\n' if '+gdal' in self.spec else 'n\n',
            # Build EEMD support (optional) into NCL?
            'n\n',
            # Build Udunits-2 support (optional) into NCL?
            'y\n' if '+uduints2' in self.spec else 'n\n',
            # Build Vis5d+ support (optional) into NCL?
            'n\n',
            # Build HDF-EOS2 support (optional) into NCL?
            'n\n',
            # Build HDF5 support (optional) into NCL?
            'y\n',
            # Build HDF-EOS5 support (optional) into NCL?
            'n\n',
            # Build GRIB2 support (optional) into NCL?
            'n\n',
            # Enter local library search path(s) :
            # The paths will be passed by the Spack wrapper.
            " \n",
            # Enter local include search path(s) :
            # All other paths will be passed by the Spack wrapper.
            "'%s'\n" % join_path(self.spec['freetype'].prefix.include,
                                 'freetype2'),
            # Go back and make more changes or review?
            'n\n',
            # Save current configuration?
            'y\n'
        ])

        config_answers_filename = 'spack-config.in'
        config_script = Executable('./Configure')

        with open(config_answers_filename, 'w') as f:
            f.writelines(config_answers)

        with open(config_answers_filename, 'r') as f:
            config_script(input=f)

    def prepare_src_tree(self):
        if '+triangle' in self.spec:
            triangle_src = join_path(self.stage.source_path, 'triangle_src')
            triangle_dst = join_path(self.stage.source_path, 'ni', 'src',
                                     'lib', 'hlu')
            copy(join_path(triangle_src, 'triangle.h'), triangle_dst)
            copy(join_path(triangle_src, 'triangle.c'), triangle_dst)

    @staticmethod
    def delete_files(*filenames):
        for filename in filenames:
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                except OSError as e:
                    raise InstallError('Failed to delete file %s: %s' % (
                        e.filename, e.strerror))
