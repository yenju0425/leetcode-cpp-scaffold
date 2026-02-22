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

namespace optimized {

class Solution {
private:
    std::optional<int> balanced_height(TreeNode* node) {
        if (!node) {
            return 0;
        }

        auto left = balanced_height(node->left);
        if (!left.has_value()) return std::nullopt;

        auto right = balanced_height(node->right);
        if (!right.has_value()) return std::nullopt;

        return std::abs(left.value() - right.value()) <= 1 ? std::make_optional(std::max(left.value(), right.value()) + 1) : std::nullopt;
    }

public:
    bool isBalanced(TreeNode* root) { return balanced_height(root).has_value(); }
};

}  // namespace optimized

}  // anonymous namespace
