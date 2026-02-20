#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    int maxProfit(std::vector<int>& prices) {
        int entry_price = std::numeric_limits<int>::max(), best_profit = 0;
        for (const auto& p : prices) {
            entry_price = std::min(entry_price, p);
            best_profit = std::max(best_profit, p - entry_price);
        }
        return best_profit;
    }
};

}  // namespace baseline

}  // anonymous namespace
