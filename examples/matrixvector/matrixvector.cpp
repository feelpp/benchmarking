#include <mpi.h>
#include <iostream>
#include <random>
#include <fstream>
#include <vector>
#include <numeric>
#include <string>
#include <filesystem>

namespace fs = std::filesystem;



void fill_matrix_vector(std::vector<double>& matrix, std::vector<double>& vector) {
    std::mt19937 gen(42);
    std::uniform_real_distribution<double> dist(0.0, 1.0);
    for (double& x : matrix) x = dist(gen);
    for (double& x : vector) x = dist(gen);
}

void matrix_vector_mult(const std::vector<double>& local_matrix, const std::vector<double>& vector, 
                        std::vector<double>& local_result, int rows_per_proc) {

}


int main(int argc, char** argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if ( argc < 3 )
    {
        if (rank == 0)
            std::cerr << "Usage: " << argv[0] << " <N> <output_directory>\n";
        MPI_Finalize();
        return 1;
    }

    int N = std::stoi(argv[1]);
    fs::path output_dir = argv[2];

    int rows_per_proc = N / size;
    std::vector<double> vector(N), local_result(rows_per_proc, 0.0);
    std::vector<double> local_matrix(rows_per_proc * N);
    std::vector<double> matrix(rank == 0 ? N * N : 0);
    std::vector<double> result(rank == 0 ? N : 0);

    double start_fill_time = MPI_Wtime();

    if (rank == 0) fill_matrix_vector(matrix, vector);

    MPI_Scatter(matrix.data(), rows_per_proc * N, MPI_DOUBLE, local_matrix.data(), rows_per_proc * N, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    MPI_Bcast(vector.data(), N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    double end_fill_time = MPI_Wtime();

    double start_time = MPI_Wtime();

    for (int i = 0; i < rows_per_proc; ++i)
        for (int j = 0; j < N; ++j)
            local_result[i] += local_matrix[i * N + j] * vector[j];

    MPI_Gather(local_result.data(), rows_per_proc, MPI_DOUBLE, result.data(), rows_per_proc, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    double end_time = MPI_Wtime();

    if (rank == 0){
        std::cout << "Fill time: " << (end_fill_time - start_fill_time) << " s\n";
        std::cout << "Compute time: " << (end_time - start_time) << " s\n";

        fs::path filename = "scalability.json";

        if (!fs::exists(output_dir))
            fs::create_directories(output_dir);

        std::ofstream scal_outfile(output_dir/filename);
        if ( scal_outfile.is_open() )
        {
            scal_outfile << "{\n";
            scal_outfile << "  \"elapsed_fill\": " << (end_fill_time - start_fill_time) << ",\n";
            scal_outfile << "  \"elapsed_compute\": " << (end_time - start_time) << "\n";
            scal_outfile << "}\n";
            scal_outfile.close();
        }
        else
            std::cerr << "[OOPSIE] Error opening file for writing." << std::endl;

    }


    MPI_Finalize();


    return 0;

}