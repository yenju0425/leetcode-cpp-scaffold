#include <gtest/gtest.h>
#include <util/io.h>
#include <util/leetcode.h>

#include <boost/json.hpp>
#include <boost/json/value_from.hpp>

#include "solution.h"

class ConstructBinaryTreeFromInorderAndPostorderTraversalParamSuite : public ::testing::TestWithParam<io::CaseParam> {
public:
    struct Adapter {
        template <class Solver>
        static boost::json::value invoke(Solver& s, const boost::json::value& case_json) {
            const auto& c     = case_json.as_object();
            const auto& input = c.at("input").as_object();

            auto inorder   = boost::json::value_to<std::vector<int>>(input.at("inorder"));
            auto postorder = boost::json::value_to<std::vector<int>>(input.at("postorder"));
            Tree tree(s.buildTree(inorder, postorder));
            return tree.serialize_tree_level_order();
        }
    };

    static inline const std::vector<io::CaseParam> kParams =
        io::build_params_from_file(__FILE__, "test_cases.json",
                                   {
                                       {"Baseline", io::make_runner<baseline::Solution, Adapter>()},
                                   });
};

TEST_P(ConstructBinaryTreeFromInorderAndPostorderTraversalParamSuite, ExampleOutput) {
    const auto& p = GetParam();
    const auto& c = p.case_json.as_object();

    boost::json::value got = p.run(p.case_json);
    EXPECT_EQ(got, c.at("output")) << "solver=" << p.solver_name << ", case=" << c.at("name").as_string().c_str();
}

INSTANTIATE_TEST_SUITE_P(FromJson, ConstructBinaryTreeFromInorderAndPostorderTraversalParamSuite,
                         ::testing::ValuesIn(ConstructBinaryTreeFromInorderAndPostorderTraversalParamSuite::kParams), io::gen_flatten_name);
