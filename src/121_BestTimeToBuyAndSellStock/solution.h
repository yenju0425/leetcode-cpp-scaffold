#include <util/leetcode.h>

namespace baseline {

using namespace std;

class Solution {
public:
    int maxProfit(vector<int> prices){
        int buyin = std::numeric_limits<int>::max(),  max_profit = 0;
        for (auto& p : prices) {
	    buyin = std::min(buyin, p);
	    max_profit = std::max(max_profit, p - buyin);
	}
	return max_profit;
    }
};

}  // namespace baseline
