#include <util/leetcode.h>

namespace default_ {

using namespace std;
using namespace util;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> val_to_index;
        for (int i = 0; i < nums.size(); ++i) {
            int complement = target - nums[i];
            if (val_to_index.contains(complement)) {
                return {val_to_index.at(complement), i};
            }
            val_to_index[nums[i]] = i;
        }

        return {0, 0};
    }
};

}  // namespace default_
