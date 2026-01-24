#ifndef UTIL_IO_H
#define UTIL_IO_H

#include <gtest/gtest.h>

#include <boost/json.hpp>
#include <string>

namespace util {

boost::json::value load_json(const std::string& filepath);

std::string path_relative_to_file(const std::string& file_path, const std::string& relative_path);

boost::json::value load_json_relative(const std::string& file_path, const std::string& relative_path);

boost::json::array load_test_cases_relative(const std::string& file_path, const std::string& relative_path);

std::string gen_test_name(const ::testing::TestParamInfo<boost::json::value>& info);

}  // namespace util

#endif /* UTIL_IO_H */
