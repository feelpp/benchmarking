#include <mpi.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <numeric>
#include <string>
#include <filesystem>

namespace fs = std::filesystem;

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    if (argc < 3) {
        if (rank == 0) {
            std::cerr << "Usage: " << argv[0] << " <N> <output_directory>\n";
        }
        MPI_Finalize();
        return 1;
    }
    int N = std::stoi(argv[1]);
    fs::path output_dir = argv[2];
    int base_chunk_size = N / size;
    int remainder = N % size;

    int local_start = rank * base_chunk_size + std::min(rank, remainder);
    int local_end = local_start + base_chunk_size + (rank < remainder ? 1 : 0);

    std::vector<double> local_array(local_end - local_start, 1.0);

    double start_time = MPI_Wtime();
    double local_sum = std::accumulate(local_array.begin(), local_array.end(), 0.0);
    double end_time = MPI_Wtime();

    double start_comm_time = MPI_Wtime();
    double global_sum = 0.0;
    MPI_Reduce(&local_sum, &global_sum, 1, MPI_DOUBLE, MPI_SUM, 0, MPI_COMM_WORLD);
    double end_comm_time = MPI_Wtime();
    if (rank == 0) {
        double computation_time = end_time - start_time;
        double communication_time = end_comm_time - start_comm_time;
        std::cout << "Global sum = " << global_sum << "\n";
        std::cout << "Computation time: " << computation_time << " seconds\n";
        std::cout << "Communication time: " << communication_time << " seconds\n";

        if (!fs::exists(output_dir))
            fs::create_directory(output_dir);

        fs::path filename = "scalability.json";

        std::ofstream outfile(output_dir/filename);
        if (outfile.is_open()) {
            outfile << "{\n";
            outfile << "  \"computation_time\": " << computation_time << ",\n";
            outfile << "  \"communication_time\": " << communication_time << ",\n";
            outfile << "  \"num_processes\": " << size << ",\n";
            outfile << "  \"N\": " << N << ",\n";
            outfile << "  \"sum\": " << global_sum << "\n";
            outfile << "}\n";
            outfile.close();
        } else {
            std::cerr << "Error opening file for writing.\n";
        }
    }

    MPI_Finalize();
    return 0;
}