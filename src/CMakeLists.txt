###  TEMPLATE.txt.tpl; coding: utf-8 ---

#  Author(s): Christophe Prud'homme <christophe.prudhomme@feelpp.org>
#       Date: 2020-06-03
#
#  Copyright (C) 2020 Cemosis
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
feelpp_add_application(laplacian SRCS laplacian.cpp TESTS INSTALL )
feelpp_add_testcase(cases PREFIX fp CATEGORY feelpp)

if(FEELPP_TOOLBOXES_FOUND)
    feelpp_add_application(toolbox SRCS toolbox.cpp LINK_LIBRARIES Feelpp::feelpp_toolbox_electric_lib TESTS)
    feelpp_add_testcase(cases)
endif()

if ( SKBUILD_PROJECT_NAME )
    python_add_library(_laplacian MODULE _laplacian.cpp WITH_SOABI)
    target_link_libraries(_laplacian PRIVATE pybind11::headers Feelpp::feelpp)
    target_compile_definitions(_laplacian PRIVATE VERSION_INFO=${PROJECT_VERSION})

    install(TARGETS _laplacian DESTINATION benchmarking)
else()
    feelpp_add_pymodule(laplacian SRCS _laplacian.cpp DESTINATION ${PROJECT_NAME})
    file(GLOB PYFILES "${CMAKE_CURRENT_SOURCE_DIR}/benchmarking/*.py")
    install(FILES ${PYFILES} DESTINATION ${FEELPP_PYTHON_MODULE_PATH}/${PROJECT_NAME})
endif()

