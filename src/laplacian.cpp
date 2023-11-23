//! -*- mode: c++; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; c-basic-offset: 4; show-trailing-whitespace: t  -*- vim:fenc=utf-8:ft=cpp:et:sw=4:ts=4:sts=4
//!
//! This file is part of the Feel++ library
//!
//! This library is free software; you can redistribute it and/or
//! modify it under the terms of the GNU Lesser General Public
//! License as published by the Free Software Foundation; either
//! version 2.1 of the License, or (at your option) any later version.
//!
//! This library is distributed in the hope that it will be useful,
//! but WITHOUT ANY WARRANTY; without even the implied warranty of
//! MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//! Lesser General Public License for more details.
//!
//! You should have received a copy of the GNU Lesser General Public
//! License along with this library; if not, write to the Free Software
//! Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
//!
//! @file
//! @author Christophe Prud'homme <christophe.prudhomme@cemosis.fr>
//! @date 2023-10-31
//! @copyright 2023 Feel++ Consortium
//! @copyright 2023 Université de Strasbourg
//!
#include "laplacian.hpp"

int main(int argc, char** argv)
{
    using namespace Feel;
    int status;
    try
    {
        Environment env(_argc = argc, _argv = argv,
                        _desc = makeOptions(),
                        _about = about(_name = fmt::format("laplacian-{}dp{}", FEELPP_DIM, FEELPP_ORDER),
                                       _author = "Feel++ Consortium",
                                       _email = "feelpp@cemosis.fr"));
        auto jsonfile = removeComments(readFromFile(Environment::expand(soption("specs"))));
        std::istringstream istr(jsonfile);
        json specs = json::parse(istr);

        // Create an instance of the Laplacian class
        Laplacian<FEELPP_DIM, FEELPP_ORDER> laplacian(specs);

        // Call the run method on the Laplacian instance
        laplacian.run();
    }
    catch (...)
    {
        handleExceptions();
    }
    return 0;
}
