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

namespace optimized {

class Solution {
public:
    int minDepth(TreeNode* root) {
        if (!root) {
            return 0;
        }

        if (!root->left) {
            return minDepth(root->right) + 1;
        }

        if (!root->right) {
            return minDepth(root->left) + 1;
        }

        return std::min(minDepth(root->left), minDepth(root->right)) + 1;
    }
};

}  // namespace optimized

}  // anonymous namespace
