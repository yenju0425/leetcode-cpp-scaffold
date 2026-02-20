#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    std::vector<std::vector<int>> levelOrder(TreeNode* root) {
        if (!root) {
            return {};
        }

        std::vector<std::vector<int>> res;

        std::queue<TreeNode*> q;
        q.push(root);

        while (!q.empty()) {
            std::vector<int> level_values;
            std::queue<TreeNode*> next_q;

            while (!q.empty()) {
                auto* node_ptr = q.front();
                level_values.push_back(node_ptr->val);

                if (node_ptr->left) next_q.push(node_ptr->left);
                if (node_ptr->right) next_q.push(node_ptr->right);

                q.pop();
            }

            res.push_back(std::move(level_values));
            std::swap(next_q, q);
        }

        return res;
    }
};

}  // namespace baseline

namespace baseline_optimized {

class Solution {
public:
    std::vector<std::vector<int>> levelOrder(TreeNode* root) {
        if (!root) {
            return {};
        }

        std::vector<std::vector<int>> res;

        std::queue<TreeNode*> q;
        q.push(root);

        while (!q.empty()) {
            std::vector<int> level_values;

            auto level_count = q.size();
            for (size_t i = 0; i < level_count; ++i) {
                auto* node_ptr = q.front();
                q.pop();

                level_values.push_back(node_ptr->val);

                if (node_ptr->left) q.push(node_ptr->left);
                if (node_ptr->right) q.push(node_ptr->right);
            }

            res.push_back(std::move(level_values));
        }

        return res;
    }
};

}  // namespace baseline_optimized

namespace dfs {

class Solution {
private:
    void dfs(TreeNode* node, size_t level, std::vector<std::vector<int>>& res) {
        if (!node) {
            return;
        }

        if (level >= res.size()) {
            res.resize(level + 1);
        }

        res[level].push_back(node->val);
        dfs(node->left, level + 1, res);
        dfs(node->right, level + 1, res);
    }

public:
    std::vector<std::vector<int>> levelOrder(TreeNode* root) {
        std::vector<std::vector<int>> res;
        dfs(root, 0, res);
        return res;
    }
};

}  // namespace dfs

}  // anonymous namespace
