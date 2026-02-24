#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    bool hasPathSum(TreeNode* root, int targetSum) {
        if (!root) {
            return false;
        }

        auto remain = targetSum - root->val;
        return (!root->left && !root->right && remain == 0) || (root->left && hasPathSum(root->left, remain)) ||
               (root->right && hasPathSum(root->right, remain));
    }
};

}  // namespace baseline

}  // anonymous namespace
