// Demo CLI that creates threads and uses atomics.
//
// Compile with the wasi-sdk:
//
//   ${WASI_SDK_PATH}/bin/clang++ -pthread --target=wasm32-wasi-threads --sysroot=${WASI_SYSROOT} -matomics -Wl,--import-memory,--export-memory,--initial-memory=8388608,--max-memory=4294967296,--shared-memory -fno-exceptions -Os threads.cxx

#include <sstream>
#include <iostream>
#include <atomic>
#include <thread>
#include <vector>


int main(int argc, char * argv[])
{
  int num_threads = 4;
  if (argc > 1)
  {
    num_threads = std::stoi(argv[1]);
  }

  std::vector<std::thread> threads;
  threads.reserve(num_threads);

  std::atomic<int> created_threads(0);

  for (int i = 0; i < num_threads; ++i)
  {
    threads.emplace_back([i, &created_threads]()
    {
      created_threads++;
    });
  }

  for (auto &t : threads)
  {
    t.join();
  }

  std::cout << "Created " << created_threads << " threads." << std::endl;

  if (created_threads == num_threads)
  {
    return EXIT_SUCCESS;
  }
  return EXIT_FAILURE;
}
