cmake_minimum_required(VERSION 3.14)
project(my_project)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(GTest CONFIG QUIET)
if(NOT GTest_FOUND)
  find_package(GTest REQUIRED)       
endif()

find_package(Boost CONFIG QUIET COMPONENTS json)
if(NOT Boost_FOUND)
  find_package(Boost REQUIRED COMPONENTS json)
endif()

message(STATUS "Boost version: ${Boost_VERSION}")
file(GLOB_RECURSE TEST_SOURCES
    CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp"
)

file(GLOB UTIL_SOURCES
    CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/util/*.cpp"
)

message(STATUS "Test source files:")
foreach(TEST_SOURCE ${TEST_SOURCES})
    message(STATUS "  ${TEST_SOURCE}")
endforeach()

add_executable(unit_test ${TEST_SOURCES} ${UTIL_SOURCES})
target_include_directories(unit_test PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(unit_test PRIVATE GTest::gtest_main Boost::json)
# gmock：target_link_libraries(unit_test PRIVATE GTest::gmock_main)

find_program(CPPCHECK cppcheck)
if(CPPCHECK)
    add_custom_target(
        cppcheck
        COMMAND ${CPPCHECK}
            --project=${CMAKE_BINARY_DIR}/compile_commands.json
            --enable=warning,style,performance,portability
            --error-exitcode=1
            --std=c++23
            --suppress=unmatchedSuppression
            --suppress=noExplicitConstructor
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        COMMENT "Running cppcheck static analysis..."
    )
    message(STATUS "cppcheck found: ${CPPCHECK}")
else()
    message(WARNING "cppcheck not found. Install with: sudo apt install cppcheck")
endif()

# enable_testing()
# include(GoogleTest)
# gtest_discover_tests(unit_test)   # 或 gtest_add_tests(unit_test ...)
