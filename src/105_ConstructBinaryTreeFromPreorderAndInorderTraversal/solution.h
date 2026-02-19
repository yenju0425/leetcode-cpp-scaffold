#include <util/leetcode.h>

namespace baseline {

using namespace std;

class Solution {
public:
    TreeNode* build(const vector<int>& preorder, const vector<int>& inorder, size_t pre_idx, size_t in_l, size_t in_r) {
        if (in_l == in_r) {
            return nullptr;
        }

        auto node_val = preorder[pre_idx];
        auto* node    = new TreeNode(node_val);

        auto idx = 0;
        for (idx = in_l; idx < in_r; ++idx) {
            if (inorder[idx] == node_val) break;
        }

        node->left  = build(preorder, inorder, pre_idx + 1, in_l, idx);
        node->right = build(preorder, inorder, pre_idx + 1 + idx - in_l, idx + 1, in_r);

        return node;
    }

public:
    TreeNode* buildTree(vector<int>& preorder, vector<int>& inorder) { return build(preorder, inorder, 0, 0, inorder.size()); }
};

}  // namespace baseline
