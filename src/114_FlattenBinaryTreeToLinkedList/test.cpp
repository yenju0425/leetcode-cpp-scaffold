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

using FlattenBinaryTreeToLinkedListParamSuite_Baseline    = FlattenBinaryTreeToLinkedListParamSuite<baseline::Solution>;
using FlattenBinaryTreeToLinkedListParamSuite_RecursiveV1 = FlattenBinaryTreeToLinkedListParamSuite<recursive_v1::Solution>;
using FlattenBinaryTreeToLinkedListParamSuite_RecursiveV2 = FlattenBinaryTreeToLinkedListParamSuite<recursive_v2::Solution>;

TEST_P(FlattenBinaryTreeToLinkedListParamSuite_Baseline, Works) {
    const auto& c     = GetParam().as_object();
    const auto& input = c.at("input").as_object();

    Tree tree(input.at("root"));
    solver.flatten(tree.root);

    boost::json::value got = tree.serialize_tree_level_order();

    EXPECT_EQ(got, c.at("output")) << "case=" << c.at("name").as_string();
}

TEST_P(FlattenBinaryTreeToLinkedListParamSuite_RecursiveV1, Works) {
    const auto& c     = GetParam().as_object();
    const auto& input = c.at("input").as_object();

    Tree tree(input.at("root"));
    solver.flatten(tree.root);

    boost::json::value got = tree.serialize_tree_level_order();

    EXPECT_EQ(got, c.at("output")) << "case=" << c.at("name").as_string();
}

TEST_P(FlattenBinaryTreeToLinkedListParamSuite_RecursiveV2, Works) {
    const auto& c     = GetParam().as_object();
    const auto& input = c.at("input").as_object();

    Tree tree(input.at("root"));
    solver.flatten(tree.root);

    boost::json::value got = tree.serialize_tree_level_order();

    EXPECT_EQ(got, c.at("output")) << "case=" << c.at("name").as_string();
}

INSTANTIATE_TEST_SUITE_P(FromJson, FlattenBinaryTreeToLinkedListParamSuite_Baseline, ::testing::ValuesIn(kCases), gen_test_name);
INSTANTIATE_TEST_SUITE_P(FromJson, FlattenBinaryTreeToLinkedListParamSuite_RecursiveV1, ::testing::ValuesIn(kCases), gen_test_name);
INSTANTIATE_TEST_SUITE_P(FromJson, FlattenBinaryTreeToLinkedListParamSuite_RecursiveV2, ::testing::ValuesIn(kCases), gen_test_name);
