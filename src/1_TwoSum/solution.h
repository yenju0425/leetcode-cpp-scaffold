#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    std::vector<int> twoSum(std::vector<int>& nums, int target) {
        std::unordered_map<int, size_t> val_to_index;
        for (size_t i = 0; i < nums.size(); ++i) {
            int complement = target - nums[i];

            auto it = val_to_index.find(complement);
            if (it != val_to_index.end()) {
                return {static_cast<int>(it->second), static_cast<int>(i)};
            }
            val_to_index[nums[i]] = i;
        }

        return {0, 0};
    }
};

}  // namespace baseline

}  // anonymous namespace
