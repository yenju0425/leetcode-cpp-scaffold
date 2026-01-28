#include <util/leetcode.h>

namespace baseline {

using namespace std;

class Solution {
public:
    void flatten(TreeNode* root) {
        TreeNode* curr = root;
        while (curr) {
            if (curr->left) {
                TreeNode* rightmost = curr->left;
                while (rightmost->right) {
                    rightmost = rightmost->right;
                }
                rightmost->right = curr->right;
                curr->right      = curr->left;
                curr->left       = nullptr;
            }
            curr = curr->right;
        }
    }
};

}  // namespace baseline

namespace recursive_v1 {

class Solution {
private:
    TreeNode* _prev = nullptr;

public:
    void flatten(TreeNode* root) {
        if (!root) {
            return;
        }

        flatten(root->right);
        flatten(root->left);

        root->right = _prev;
        root->left  = nullptr;
        _prev       = root;
    }
};

}  // namespace recursive_v1

namespace recursive_v2 {

class Solution {
private:
    TreeNode* _prev = nullptr;

public:
    void flatten(TreeNode* root) {
        if (!root) {
            return;
        }

        _prev = root;

        flatten(root->left);
        if (_prev != root) {
            _prev->right = root->right;
            root->right  = root->left;
            root->left   = nullptr;
        }

        flatten(_prev->right);
    }
};

}  // namespace recursive_v2
