#include <gtest/gtest.h>
#include <util/leetcode.h>

#include <boost/json.hpp>

#include "solution.h"

static const boost::json::array kCases = load_test_cases_relative(__FILE__, "test_cases.json");

template <class SolverT>
class FlattenBinaryTreeToLinkedListParamSuite : public ::testing::TestWithParam<boost::json::value> {
protected:
    SolverT solver;
};

using FlattenBinaryTreeToLinkedListParamSuite_Default = FlattenBinaryTreeToLinkedListParamSuite<default_::Solution>;

TEST_P(FlattenBinaryTreeToLinkedListParamSuite_Default, Works) {
    const auto& c     = GetParam().as_object();
    const auto& input = c.at("input").as_object();

    TreeNode* root = build_tree_level_order(input.at("root"));
    solver.flatten(root);

    boost::json::value got = dump_tree_level_order(root);

    EXPECT_EQ(got, c.at("output")) << "case=" << c.at("name").as_string();
}

INSTANTIATE_TEST_SUITE_P(FromJson, FlattenBinaryTreeToLinkedListParamSuite_Default, ::testing::ValuesIn(kCases),
                         gen_test_name);
