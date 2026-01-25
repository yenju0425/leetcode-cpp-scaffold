#include "io.h"

#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>

boost::json::value load_json(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    return boost::json::parse(buffer.str());
}

std::string path_relative_to_file(const std::string& file_path, const std::string& relative_path) {
    return (std::filesystem::path(file_path).parent_path() / relative_path).string();
}

boost::json::value load_json_relative(const std::string& file_path, const std::string& relative_path) {
    return load_json(path_relative_to_file(file_path, relative_path));
}

boost::json::array load_test_cases_relative(const std::string& file_path, const std::string& relative_path) {
    boost::json::value jv = load_json_relative(file_path, relative_path);
    return jv.as_object().at("test_cases").as_array();
}

std::string gen_test_name(const ::testing::TestParamInfo<boost::json::value>& info) {
    const auto& obj = info.param.as_object();
    if (obj.contains("name")) {
        return std::string(obj.at("name").as_string());
    }
    return std::to_string(info.index);
}
