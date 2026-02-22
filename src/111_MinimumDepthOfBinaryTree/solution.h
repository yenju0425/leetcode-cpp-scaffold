#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    int minDepth(TreeNode* root) {
        if (!root) {
            return std::numeric_limits<int>::max();
        }

        if (!root->left && !root->right) {
            return 1;
        }

        return std::min(minDepth(root->left), minDepth(root->right)) + 1;
    }
};

}  // namespace baseline

}  // anonymous namespace
