#include <gtest/gtest.h>
#include <util/leetcode.h>

#include <boost/json.hpp>

#include "solution.h"

static const boost::json::array kCases = load_test_cases_relative(__FILE__, "test_cases.json");

template <class SolverT>
class SameTreeParamSuite : public ::testing::TestWithParam<boost::json::value> {
protected:
    SolverT solver;
};

using SameTreeParamSuite_Default = SameTreeParamSuite<default_::Solution>;

TEST_P(SameTreeParamSuite_Default, Works) {
    const auto& c     = GetParam().as_object();
    const auto& input = c.at("input").as_object();

    TreeNode* p = build_tree_level_order(input.at("p"));
    TreeNode* q = build_tree_level_order(input.at("q"));

    boost::json::value got = boost::json::value_from(solver.isSameTree(p, q));

    EXPECT_EQ(got, c.at("output")) << "case=" << c.at("name").as_string();
}

INSTANTIATE_TEST_SUITE_P(FromJson, SameTreeParamSuite_Default, ::testing::ValuesIn(kCases), gen_test_name);
