##############################################################################
# Copyright (c) 2013-2017, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Spack.
# Created by Todd Gamblin, tgamblin@llnl.gov, All rights reserved.
# LLNL-CODE-647188
#
# For details, see https://github.com/spack/spack
# Please also see the NOTICE and LICENSE files for our notice and the LGPL.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (as
# published by the Free Software Foundation) version 2.1, February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the terms and
# conditions of the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##############################################################################
from spack import *


class AllineaForge(Package):
    """Allinea Forge is the complete toolsuite for software development - with
    everything needed to debug, profile, optimize, edit and build C, C++ and
    Fortran applications on Linux for high performance - from single threads
    through to complex parallel HPC codes with MPI, OpenMP, threads or CUDA."""

    homepage = "http://www.allinea.com/products/develop-allinea-forge"

    version('6.0.4', 'df7f769975048477a36f208d0cd57d7e')

    # Licensing
    license_required = True
    license_comment = '#'
    license_files = ['licences/Licence']
    license_vars = ['ALLINEA_LICENCE_FILE', 'ALLINEA_LICENSE_FILE']
    license_url = 'http://www.allinea.com/user-guide/forge/Installation.html'

    @property
    def allinea_os_name(self):
        allinea_os_names = {
            "rhel6": "Redhat-6.0-x86_64",
            "sles12": "Suse-12-x86_64",
            "unknown": "Unknown-OS",
            }
        return allinea_os_names[self.platform_os]

    @property
    def platform_os(self):
        try:
            return self.spec.architecture.platform_os
        except:
            return "unknown"
   
    def url_for_version(self, version):
        url = "http://content.allinea.com/downloads/"
        return url + "allinea-forge-%s-%s.tar" % (version, self.allinea_os_name)

    def install(self, spec, prefix):
        textinstall = Executable('./textinstall.sh')
        textinstall('--accept-licence', prefix)
