###  TEMPLATE.txt.tpl; coding: utf-8 ---

#  Author(s): Christophe Prud'homme <christophe.prudhomme@feelpp.org>
#       Date: 2020-06-03
#
#  Copyright (C) 2020-present Cemosis
#
# Distributed under the GPL(GNU Public License):
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#
cmake_minimum_required(VERSION 3.21.0)

project(
  feelpp-project
  VERSION 3.0.1 )

set(EXTRA_VERSION "")
set(PROJECT_SHORTNAME "fp")

include(GNUInstallDirs)

if (POLICY CMP0077)
  cmake_policy(SET CMP0077 NEW)
  set(CMAKE_POLICY_DEFAULT_CMP0077 NEW)
endif()

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

find_package(Feel++ COMPONENTS Toolboxes PATHS ${FEELPP_DIR}/share/feelpp/feel/cmake/modules $ENV{FEELPP_DIR}/share/feelpp/feel/cmake/modules /usr/share/feelpp/feel/cmake/modules /usr/local/share/feelpp/feel/cmake/modules )
if(NOT FEELPP_FOUND)
  message(FATAL_ERROR "Feel++ was not found on your system. Make sure to install it and specify the FEELPP_DIR to reference the installation directory.")
endif()
if ( NOT FEELPP_TOOLBOXES_FOUND )
  message(WARNING "Feel++ Toolboxes SDK is not found on your system. The toolbox application is now disabled.")
endif()

enable_testing()

if ( NOT TARGET check )
  add_custom_target(check)
endif()


add_subdirectory( src )
#add_subdirectory( docs )

# extra ignored files
list(APPEND CPACK_SOURCE_IGNORE_FILES
  .git
  .gitignore
  .travis.yml
  .appveyor.yml
  )

set(CPACK_PACKAGE_NAME "${PROJECT_NAME}-${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}${EXTRA_VERSION}")
set(CPACK_SOURCE_PACKAGE_FILE_NAME "${PROJECT_NAME}-${PROJECT_VERSION}${EXTRA_VERSION}")
SET(CPACK_PACKAGE_FILE_NAME "${PROJECT_NAME}-${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}.${PROJECT_VERSION_PATCH}${EXTRA_VERSION}-${CMAKE_SYSTEM_NAME}")
set(CPACK_PACKAGE_DIRECTORY "${PROJECT_BINARY_DIR}/assets")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Cemosis feelpp-project template application")
set(CPACK_PACKAGE_DESCRIPTION "Cemosis provides a Feel++ template application.")
set(CPACK_PACKAGE_VENDOR "Cemosis")
set(CPACK_PACKAGE_CONTACT "Christophe Prud'homme <christophe.prudhomme@cemosis.fr>")
set(CPACK_PACKAGE_VERSION_MAJOR "${PROJECT_VERSION_MAJOR}")
set(CPACK_PACKAGE_VERSION_MINOR "${PROJECT_VERSION_MINOR}")
set(CPACK_PACKAGE_VERSION_PATCH "${PROJECT_VERSION_PATCH}")


set(CPACK_GENERATOR "TGZ;DEB")
set(CPACK_SOURCE_GENERATOR "TGZ")


set(CPACK_DEBIAN_PACKAGE_NAME "${PROJECT_NAME}")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "${CPACK_PACKAGE_CONTACT}")
if ( USE_FEELPP_TOOLBOXES )
  set(CPACK_DEBIAN_PACKAGE_DEPENDS "libfeelpp1 (>= 0.109)") # add depends with relevant toolbox lib
else()
  set(CPACK_DEBIAN_PACKAGE_DEPENDS "libfeelpp1 (>= 0.109)")
endif()
set(CPACK_DEBIAN_PACKAGE_DESCRIPTION_SUMMARY "${CPACK_PACKAGE_DESCRIPTION_SUMMARY}")
set(CPACK_DEBIAN_PACKAGE_DESCRIPTION "${CPACK_PACKAGE_DESCRIPTION}")
set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
set(CPACK_DEBIAN_PACKAGE_SECTION "science")
set(CPACK_DEBIAN_PACKAGE_VERSION "${CPACK_PACKAGE_VERSION_MAJOR}.${CPACK_PACKAGE_VERSION_MINOR}.${CPACK_PACKAGE_VERSION_PATCH}${EXTRA_VERSION}")
set(CPACK_DEBIAN_ARCHITECTURE "${CMAKE_SYSTEM_PROCESSOR}")
# set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA "${CMAKE_SOURCE_DIR}/cmake/debian/postinst")
  
include(CPack)

