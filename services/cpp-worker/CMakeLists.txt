cmake_minimum_required(VERSION 3.16)

project(reactor_cpp_worker LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(reactor-cpp-worker src/main.cpp)

if(UNIX AND NOT APPLE)
    target_compile_options(reactor-cpp-worker PRIVATE -Wall -Wextra -Wpedantic)
endif()
