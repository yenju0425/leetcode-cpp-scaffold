#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
private:
    std::unordered_map<int, size_t> _in_idx;

    TreeNode* build(const std::vector<int>& inorder, const std::vector<int>& postorder, size_t post_idx, size_t in_l, size_t in_r) {
        if (in_l == in_r) {
            return nullptr;
        }

        auto node_val = postorder[post_idx];
        auto* node    = new TreeNode(node_val);

        size_t idx = _in_idx.at(node_val);

        node->left  = build(inorder, postorder, idx - 1, in_l, idx);
        node->right = build(inorder, postorder, post_idx - 1, idx + 1, in_r);

        return node;
    }

public:
    TreeNode* buildTree(std::vector<int>& inorder, std::vector<int>& postorder) {
        for (size_t i = 0; i < inorder.size(); ++i) {
            _in_idx[inorder[i]] = i;
        }

        return build(inorder, postorder, postorder.size() - 1, 0, inorder.size());
    }
};

}  // namespace baseline

}  // anonymous namespace
