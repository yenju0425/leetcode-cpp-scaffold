#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    std::vector<std::vector<int>> generate(int numRows) {
        std::vector<std::vector<int>> res;
        res.resize(numRows);
        for (int i = 0; i < numRows; ++i) {
            res[i].resize(i);
            for (int j = 0; j <= i; ++j) {
                if (j == 0 || j == i) {
                    res[i][j] = 1;
                } else {
                    res[i][j] = res[i - 1][j - 1] + res[i][j - 1];
                }
            }
        }

        return res;
    }
};

}  // namespace baseline

}  // anonymous namespace
