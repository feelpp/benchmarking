#include <feel/feelcore/environment.hpp>
#include <feel/feelmodels/electric/electric.hpp>

int main(int argc, char** argv)
{
    using namespace Feel;
    po::options_description myoptions("my options");
    myoptions.add( toolboxes_options("electric") );
    myoptions.add_options()
        ( "myexpr", po::value<std::string>()->default_value("3*x*y:x:y"), "my expression")
        ;

    Environment env( _argc=argc, _argv=argv,
                     _desc=myoptions,
                     _about=about(_name="update_toolbox",
                                  _author="Feel++ Consortium",
                                  _email="feelpp-devel@feelpp.org"));

    typedef FeelModels::Electric< Simplex<2,1>,
                                  Lagrange<1, Scalar,Continuous,PointSetFekete> > model_type;
    std::shared_ptr<model_type> electric( new model_type("electric") );
    // init the toolbox
    electric->init();
    electric->printAndSaveInfo();

    // create a lambda function
    auto lambda = [&electric](FeelModels::ModelAlgebraic::DataUpdateLinear & data) {
                      // build each time, not just for the constant part
                      bool buildCstPart = data.buildCstPart();
                      if( buildCstPart )
                          return;
                      // retrieve matrix and vector already assemble
                      sparse_matrix_ptrtype& A = data.matrix();
                      vector_ptrtype& F = data.rhs();
                      // retrieve space and create a test function
                      auto Xh = electric->spaceElectricPotential();
                      auto v = Xh->element();

                      // create a linear form from the vector on the function space
                      auto f = form1( _test=Xh, _vector=F);
                      // get an expression from the options (or from another equation)
                      auto e = expr(soption("myexpr"));
                      // add the term to the linear form
                      f += integrate( _range=elements(support(Xh)), _expr=inner(e, id(v)) );
                  };
    // add the lambda function to the algebraic factory
    electric->algebraicFactory()->addFunctionLinearAssembly(lambda);
    // solve the problem
    electric->solve();
    electric->exportResults();

    return 0;
}
