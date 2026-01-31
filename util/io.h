#ifndef UTIL_IO_H
#define UTIL_IO_H

#include <gtest/gtest.h>

#include <boost/json.hpp>
#include <string>
#include <unordered_map>

namespace io {

using RunFn = boost::json::value (*)(const boost::json::value& case_json);

struct CaseParam {
    std::string solver_name;
    RunFn run;
    const boost::json::value case_json;

    friend std::ostream& operator<<(std::ostream& os, const CaseParam& param) {
        os << "Input: " << param.case_json.at("input") << ", Output: " << param.case_json.at("output");
        return os;
    }
};

template <class Solver, class Adapter>
boost::json::value run_with_adapter(const boost::json::value& case_json) {
    Solver s;
    return Adapter::template invoke(s, case_json);
}

template <class Solver, class Adapter>
constexpr io::RunFn make_runner() {
    return &run_with_adapter<Solver, Adapter>;
}

boost::json::value load_json(const std::string& filepath);

std::string path_relative_to_file(const std::string& file_path, const std::string& relative_path);

boost::json::value load_json_relative(const std::string& file_path, const std::string& relative_path);

boost::json::array load_test_cases_relative(const std::string& file_path, const std::string& relative_path);

std::string gen_flatten_name(const ::testing::TestParamInfo<CaseParam>& info);

std::vector<io::CaseParam> build_params_from_file(const std::string& dir_path, const std::string& file_name,
                                                  const std::unordered_map<std::string, io::RunFn>& solvers);

}  // namespace io

#endif /* UTIL_IO_H */
