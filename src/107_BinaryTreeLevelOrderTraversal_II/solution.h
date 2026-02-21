#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
private:
    void dfs(TreeNode* node, size_t cur_depth, std::vector<std::vector<int>>& res) {
        if (!node) {
            return;
        }

        if (res.size() == cur_depth) {
            res.push_back({});
        }

        res[cur_depth].push_back(node->val);
        dfs(node->left, cur_depth + 1, res);
        dfs(node->right, cur_depth + 1, res);
    }

public:
    std::vector<std::vector<int>> levelOrderBottom(TreeNode* root) {
        std::vector<std::vector<int>> res;
        dfs(root, 0, res);

        std::reverse(res.begin(), res.end());
        return res;
    }
};
}  // namespace baseline

}  // anonymous namespace
