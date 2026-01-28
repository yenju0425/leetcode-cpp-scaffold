#include <util/leetcode.h>

namespace baseline {

using namespace std;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> val_to_index;
        for (int i = 0; i < nums.size(); ++i) {
            int complement = target - nums[i];

            auto it = val_to_index.find(complement);
            if (it != val_to_index.end()) {
                return {it->second, i};
            }
            val_to_index[nums[i]] = i;
        }

        return {0, 0};
    }
};

}  // namespace baseline
