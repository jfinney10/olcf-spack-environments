#!/bin/bash

#####################
# Obtain the path to this file.
#   `_THIS`  : path to this file
#   `_THIS_DIR`: path to parent directory of ${_THIS}
# First determine if script is sourced or executed
if [[ "$0" != "${BASH_SOURCE:-}" ]]; then
  # Script is sourced
  _SOURCED=1
  if [ -z "${BASH_SOURCE:-}" ]; then
    _THIS="$(which $0)"
  else
    _THIS="${BASH_SOURCE[0]}"
  fi
else
  # Script is executed
  _SOURCED=0
  _THIS="${BASH_SOURCE[0]}"
fi
while [ -h "$_THIS" ]; do
  # resolve $_THIS until the file is no longer a symlink
  _THIS_DIR="$( cd -P "$( dirname "$_THIS" )" >/dev/null && pwd )"

  # if $_THIS was a relative symlink, we need to resolve it relative to the
  # path where the symlink file was located
  _THIS="$(readlink "$_THIS")"
  [[ $_THIS != /* ]] && _THIS="$_THIS_DIR/$_THIS" 
done
_THIS_DIR="$( cd -P "$( dirname "$_THIS" )" >/dev/null && pwd )"
FACILITY_SPACK_ROOT="${_THIS_DIR/#\/autofs\/nccs-svm[0-9]_sw//sw}"
export FACILITY_SPACK_ROOT="${FACILITY_SPACK_ROOT/#\/autofs\/nccs-svm[0-9]_home[0-9]\///ccs/home/}"
#####################

# This script must be sourced.
[ ${_SOURCED} -eq 0 ] \
  && echo "ERROR: This script must be sourced!" \
  && echo "usage: '. ./init-facility-spack.sh'" \
  && exit 1

# Do nothing if a spack instance is already initialized.
[[ -n "${SPACK_ROOT:-}" ]] \
  && echo "Spack is already initialized!" \
  && echo "  '${SPACK_ROOT}'" \
  && echo "Please restart shell to change configuration." \
  && return 1

_THIS_HOST="$(hostname --long \
             | sed -e 's/\.\(olcf\|ccs\)\..*//' \
                   -e 's/[-]\?\(login\|ext\|batch\)[^\.]*[\.]\?//' \
                   -e 's/[-0-9]*$//')"

[[ "${_THIS_HOST:-XX}" == "XX" ]] \
  && echo "ERROR: Current host '${_THIS_HOST}' could not be identified!" \
  && return 1
[ ! -d "${FACILITY_SPACK_ROOT}/hosts/${_THIS_HOST}/envs/${ENV_NAME}" ] \
  && echo "ERROR: Current host '${_THIS_HOST}' does not have an environment named 'ENV_NAME=${ENV_NAME}'!" \
  && return 1

# FIXME: This should be non-user specific and inherited from the parent
# environment and possibly use an envvar-passed environment name in conjunction
# with the identified host or fallback to using the base env if a specific env is
# not given.
FACILITY_ENV_PREFIX="/sw/${_THIS_HOST}/spack-envs"
export ENV_PREFIX="${ENV_PREFIX:-${FACILITY_ENV_PREFIX}}"
export ENV_NAME="${ENV_NAME:-base}"

_HOST_CONF_DIR="${FACILITY_SPACK_ROOT}/hosts/${_THIS_HOST}"
export ENV_ROOT="${ENV_PREFIX}/${ENV_NAME}"
export ENV_LMOD_ROOT="${ENV_ROOT}/modules"

# Abort if ENV_PREFIX is not set to something the current user owns or doesn't
# exist:
[[ -z "${ENV_PREFIX:-}" ]] \
  && echo "ERROR: Environment prefix 'ENV_PREFIX=${ENV_PREFIX:-}' not set!" \
  && return 1
[[ ! -d "${ENV_PREFIX:-}" ]] \
  && echo "ERROR: Environment prefix 'ENV_PREFIX=${ENV_PREFIX:-}' does not exist!" \
  && return 1
[[ "$(stat -c '%U' ${ENV_PREFIX})" != ${USER} ]] \
  && echo "ERROR: Environment prefix 'ENV_PREFIX=${ENV_PREFIX:-}' is not owned by ${USER}!" \
  && return 1

# Copy git-tracked modules to module root.
# FIXME: Need to sync this configuration with the spack environment in use.
mkdir -p "${ENV_LMOD_ROOT}"
cp -dRu --preserve=mode,timestamps \
   "${_HOST_CONF_DIR}/share/lmod/modulefiles/static/site" \
   "${ENV_LMOD_ROOT}/."

function setup_alternate_module_environment {
  # Setup alternate module environment
  if [[ "${ENV_PREFIX:-YY}" == "${FACILITY_ENV_PREFIX:-XX}" ]]; then
    module reset
    module purge
    echo "Using facility module root"
  else
    module reset
    module purge
    echo "Using custom module root '${ENV_LMOD_ROOT}'"
    export MODULEPATH="$1"
  fi
}

# Host-specific environment modifications
case "${_THIS_HOST}" in
  peak)
    setup_alternate_module_environment "${ENV_LMOD_ROOT}/spack/linux-rhel7-ppc64le/Core:${ENV_LMOD_ROOT}/site/Core:/sw/${_THIS_HOST}/modulefiles/core"
    module load python/3.7.0-anaconda3-5.3.0
    ;;
  andes)
    setup_alternate_module_environment "${ENV_LMOD_ROOT}/spack/linux-rhel8-x86_64/Core:${ENV_LMOD_ROOT}/site/Core:/sw/${_THIS_HOST}/modulefiles/core"
    ;;
  *)
    ;;
esac

export PYTHONDONTWRITEBYTECODE=1
# FIXME - ensure spack instance is checked out to appropriate commit
# WARNING - checking out new branches of spack while other instances are using
#           it will certainly cause problems. Need a way to lock the spack repo
#           while it is in use.
source "${FACILITY_SPACK_ROOT}/spack/share/spack/setup-env.sh"
echo "Spack initialized for ${_THIS_HOST:-Unknown host} at ${SPACK_ROOT}"
spack env activate -d "${_HOST_CONF_DIR}/envs/${ENV_NAME}"
