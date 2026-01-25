#include <gtest/gtest.h>
#include <util/leetcode.h>

#include <boost/json.hpp>
#include <boost/json/value_from.hpp>

#include "solution.h"

using namespace util;

static const boost::json::array kCases = util::load_test_cases_relative(__FILE__, "test_cases.json");

template <class SolverT>
class TwoSumParamSuite : public ::testing::TestWithParam<boost::json::value> {
protected:
    SolverT solver;
};

using TwoSumParamSuite_Default = TwoSumParamSuite<default_::Solution>;

TEST_P(TwoSumParamSuite_Default, Works) {
    const auto& c     = GetParam().as_object();
    const auto& input = c.at("input").as_object();

    auto nums        = boost::json::value_to<std::vector<int>>(input.at("nums"));
    const int target = boost::json::value_to<int>(input.at("target"));

    boost::json::value got = boost::json::value_from(solver.twoSum(nums, target));

    EXPECT_EQ(got, c.at("output")) << "case=" << c.at("name").as_string();
}

INSTANTIATE_TEST_SUITE_P(FromJson, TwoSumParamSuite_Default, ::testing::ValuesIn(kCases), util::gen_test_name);
