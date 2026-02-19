#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
public:
    std::vector<std::vector<int>> zigzagLevelOrder(TreeNode* root) {
        if (!root) {
            return {};
        }

        std::vector<std::vector<int>> res;

        std::deque<TreeNode*> q;
        q.push_back(root);

        while (!q.empty()) {
            std::vector<int> level_values;

            auto level_count = q.size();
            for (size_t i = 0; i < level_count; ++i) {
                TreeNode* node;

                if (res.size() % 2) {
                    node = q.back();
                    q.pop_back();

                    if (node->right) {
                        q.push_front(node->right);
                    }

                    if (node->left) {
                        q.push_front(node->left);
                    }

                } else {
                    node = q.front();
                    q.pop_front();

                    if (node->left) {
                        q.push_back(node->left);
                    }

                    if (node->right) {
                        q.push_back(node->right);
                    }
                }

                level_values.push_back(node->val);
            }

            res.push_back(std::move(level_values));
        }

        return res;
    }
};

}  // namespace baseline

}  // anonymous namespace
