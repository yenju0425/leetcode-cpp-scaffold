#include <util/leetcode.h>

namespace baseline {

using namespace std;

class Solution {
private:
    bool isSameTree(TreeNode* p, TreeNode* q) {
        return (!p && !q) || (p && q && p->val == q->val && isSameTree(p->left, q->left) && isSameTree(p->right, q->right));
    }

    void invertTree(TreeNode* root) {
        if (root == nullptr) {
            return;
        }

        std::swap(root->left, root->right);
        invertTree(root->left);
        invertTree(root->right);
    }

public:
    bool isSymmetric(TreeNode* root) {
        invertTree(root->right);
        return isSameTree(root->left, root->right);
    }
};

}  // namespace baseline

namespace bfs {

class Solution {
public:
    bool isSymmetric(TreeNode* root) {
        if (!root) {
            return true;
        }

        std::queue<TreeNode*> q;
        q.push(root->left);
        q.push(root->right);

        while (!q.empty()) {
            std::vector<TreeNode*> temp;
            temp.reserve(q.size());

            while (!q.empty()) {
                temp.push_back(q.front());
                q.pop();
            }

            size_t level_size = temp.size();
            if (level_size % 2 != 0) {
                return false;
            }

            for (size_t i = 0; i < level_size / 2; ++i) {
                const TreeNode* front = temp[i];
                const TreeNode* back  = temp[level_size - 1 - i];

                if ((front && !back) || (!front && back) || (front && back && front->val != back->val)) {
                    return false;
                }
            }

            for (auto node : temp) {
                if (node) {
                    q.push(node->left);
                    q.push(node->right);
                }
            }
        }

        return true;
    }
};

}  // namespace bfs

namespace bfs_optimized {

class Solution {
public:
    bool isSymmetric(TreeNode* root) {
        if (!root) return true;

        std::queue<std::pair<TreeNode*, TreeNode*>> pending;
        pending.push({root->left, root->right});

        while (!pending.empty()) {
            auto [lhs, rhs] = pending.front();
            pending.pop();

            if (!lhs && !rhs) continue;
            if (!lhs || !rhs) return false;
            if (lhs->val != rhs->val) return false;

            pending.push({lhs->left, rhs->right});
            pending.push({lhs->right, rhs->left});
        }

        return true;
    }
};

}  // namespace bfs_optimized
