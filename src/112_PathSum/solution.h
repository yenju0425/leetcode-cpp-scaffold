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

namespace optimized {

class Solution {
private:
    bool dfs(TreeNode* root, int remain) {
        if (!root) {
            return remain == 0;
        }

        remain -= root->val;
        return dfs(root->left, remain) || dfs(root->right, remain);
    }

public:
    bool hasPathSum(TreeNode* root, int targetSum) {
        if (!root) {
            return false;
        }

        return dfs(root, targetSum);
    }
};

}  // namespace optimized

}  // anonymous namespace
