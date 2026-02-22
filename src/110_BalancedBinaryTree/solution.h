#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
private:
    int height(TreeNode* node) {
        if (!node) {
            return 0;
        }

        return std::max(height(node->left), height(node->right)) + 1;
    }

public:
    bool isBalanced(TreeNode* root) {
        if (!root) {
            return true;
        }

        return (std::abs(height(root->left) - height(root->right)) <= 1) && isBalanced(root->left) && isBalanced(root->right);
    }
};

}  // namespace baseline

}  // anonymous namespace
