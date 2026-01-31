#include "io.h"

#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>

boost::json::value io::load_json(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    std::stringstream buffer;
    buffer << file.rdbuf();
    return boost::json::parse(buffer.str());
}

std::string io::path_relative_to_file(const std::string& file_path, const std::string& relative_path) {
    return (std::filesystem::path(file_path).parent_path() / relative_path).string();
}

boost::json::value io::load_json_relative(const std::string& file_path, const std::string& relative_path) {
    return load_json(path_relative_to_file(file_path, relative_path));
}

boost::json::array io::load_test_cases_relative(const std::string& file_path, const std::string& relative_path) {
    boost::json::value jv = load_json_relative(file_path, relative_path);
    return jv.as_object().at("test_cases").as_array();
}

std::string io::gen_flatten_name(const ::testing::TestParamInfo<CaseParam>& info) {
    const auto& c = info.param.case_json.as_object();

    std::string name = std::string(info.param.solver_name) + "_" + std::string(c.at("name").as_string().c_str());

    for (auto& ch : name) {
        if (!(std::isalnum(static_cast<unsigned char>(ch)) || ch == '_')) ch = '_';
    }
    if (name.empty() || !(std::isalpha(static_cast<unsigned char>(name[0])) || name[0] == '_')) {
        name.insert(name.begin(), '_');
    }
    return name;
}

std::vector<io::CaseParam> io::build_params_from_file(const std::string& dir_path, const std::string& file_name,
                                                      const std::unordered_map<std::string, io::RunFn>& solvers) {
    const boost::json::array cases = io::load_test_cases_relative(dir_path, file_name);

    std::vector<io::CaseParam> out;
    out.reserve(cases.size() * solvers.size());

    for (const auto& c : cases) {
        for (const auto& [name, fn] : solvers) {
            out.push_back(io::CaseParam{name, fn, c});
        }
    }
    return out;
}
