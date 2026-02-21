#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
private:
    TreeNode* build(const std::vector<int>& nums, size_t left, size_t right) {
        if (left >= right) {
            return nullptr;
        }

        auto mid = (left + right) / 2;

        auto val       = nums[mid];
        TreeNode* node = new TreeNode(val);

        node->left  = build(nums, left, mid);
        node->right = build(nums, mid + 1, right);

        return node;
    }

public:
    TreeNode* sortedArrayToBST(std::vector<int>& nums) { return build(nums, 0, nums.size()); }
};

}  // namespace baseline

}  // anonymous namespace
