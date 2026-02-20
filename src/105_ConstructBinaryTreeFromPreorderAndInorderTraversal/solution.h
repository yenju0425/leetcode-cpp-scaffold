#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
private:
    TreeNode* build(const std::vector<int>& preorder, const std::vector<int>& inorder, size_t pre_idx, size_t in_l, size_t in_r) {
        if (in_l == in_r) {
            return nullptr;
        }

        auto node_val = preorder[pre_idx];
        auto* node    = new TreeNode(node_val);

        size_t idx = in_l;
        while (idx < in_r && inorder[idx] != node_val) ++idx;

        node->left  = build(preorder, inorder, pre_idx + 1, in_l, idx);
        node->right = build(preorder, inorder, pre_idx + 1 + idx - in_l, idx + 1, in_r);

        return node;
    }

public:
    TreeNode* buildTree(std::vector<int>& preorder, std::vector<int>& inorder) { return build(preorder, inorder, 0, 0, inorder.size()); }
};

}  // namespace baseline

namespace hashmap {

class Solution {
private:
    std::unordered_map<int, size_t> _in_idx;

    TreeNode* build(const std::vector<int>& preorder, const std::vector<int>& inorder, size_t pre_idx, size_t in_l, size_t in_r) {
        if (in_l == in_r) {
            return nullptr;
        }

        auto node_val = preorder[pre_idx];
        auto* node    = new TreeNode(node_val);

        size_t idx = _in_idx.at(node_val);

        node->left  = build(preorder, inorder, pre_idx + 1, in_l, idx);
        node->right = build(preorder, inorder, pre_idx + 1 + idx - in_l, idx + 1, in_r);

        return node;
    }

public:
    TreeNode* buildTree(std::vector<int>& preorder, std::vector<int>& inorder) {
        for (size_t i = 0; i < inorder.size(); ++i) {
            _in_idx[inorder[i]] = i;
        }

        return build(preorder, inorder, 0, 0, inorder.size());
    }
};

}  // namespace hashmap

}  // anonymous namespace
