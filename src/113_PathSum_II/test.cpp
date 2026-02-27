#include <gtest/gtest.h>
#include <util/io.h>
#include <util/leetcode.h>

#include <boost/json.hpp>

#include "solution.h"

class PathSum_IIParamSuite : public ::testing::TestWithParam<io::CaseParam> {
public:
    struct Adapter {
        template <class Solver>
        static boost::json::value invoke(Solver& s, const boost::json::value& case_json) {
            const auto& c     = case_json.as_object();
            const auto& input = c.at("input").as_object();

            Tree tree(input.at("root"));
            auto target = input.at("targetSum").to_number<int>();
            return boost::json::value_from(s.pathSum(tree.root(), target));
        }
    };

    static inline const std::vector<io::CaseParam> kParams =
        io::build_params_from_file(__FILE__, "test_cases.json",
                                   {
                                       {"Baseline", io::make_runner<baseline::Solution, Adapter>()},
                                       {"Optimized", io::make_runner<optimized::Solution, Adapter>()},
                                   });
};

TEST_P(PathSum_IIParamSuite, ExampleOutput) {
    const auto& p = GetParam();
    const auto& c = p.case_json.as_object();

    boost::json::value got = p.run(p.case_json);
    EXPECT_EQ(got, c.at("output")) << "solver=" << p.solver_name << ", case=" << c.at("name").as_string().c_str();
}

INSTANTIATE_TEST_SUITE_P(FromJson, PathSum_IIParamSuite, ::testing::ValuesIn(PathSum_IIParamSuite::kParams), io::gen_flatten_name);
