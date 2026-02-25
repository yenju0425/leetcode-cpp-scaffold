#include <util/leetcode.h>

namespace {

namespace baseline {

class Solution {
private:
    void search_path(TreeNode* root, int target, std::vector<int> cur_path, std::vector<std::vector<int>>& paths) {
        if (!root) {
            return;
        }

        auto remain = target - root->val;
        cur_path.push_back(root->val);

        if (!root->left && !root->right) {
            if (remain == 0) {
                paths.push_back(std::move(cur_path));
            }
            return;
        }

        if (root->left) {
            search_path(root->left, remain, cur_path, paths);
        }

        if (root->right) {
            search_path(root->right, remain, cur_path, paths);
        }
    }

public:
    std::vector<std::vector<int>> pathSum(TreeNode* root, int targetSum) {
        std::vector<std::vector<int>> paths;
        search_path(root, targetSum, {}, paths);
        return paths;
    }
};

}  // namespace baseline

namespace optimized {

class Solution {
private:
    void search_path(TreeNode* root, int target, std::vector<int>& cur_path, std::vector<std::vector<int>>& paths) {
        if (!root) {
            return;
        }

        auto remain = target - root->val;
        cur_path.push_back(root->val);

        if (!root->left && !root->right) {
            if (remain == 0) {
                paths.push_back(cur_path);
            }
        } else {
            search_path(root->left, remain, cur_path, paths);
            search_path(root->right, remain, cur_path, paths);
        }
        cur_path.pop_back();
    }

public:
    std::vector<std::vector<int>> pathSum(TreeNode* root, int targetSum) {
        std::vector<int> cur_path;
        std::vector<std::vector<int>> paths;
        search_path(root, targetSum, cur_path, paths);
        return paths;
    }
};

}  // namespace optimized

}  // anonymous namespace
