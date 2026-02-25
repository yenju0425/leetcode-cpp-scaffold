#include <util/leetcode.h>

namespace {

namespace baseline {

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

namespace recursive_v3 {

class Solution {
public:
    void flatten(TreeNode* root) {
        if (!root) {
            return;
        }

        flatten(root->left);
        flatten(root->right);
        if (root->left) {
            auto* node = root->left;
            while (node->right) {
                node = node->right;
            }

            node->right = root->right;
            root->right = root->left;
            root->left  = nullptr;
        }
    }
};

}  // namespace recursive_v3

namespace recursive_v4 {

class Solution {
private:
    TreeNode* flatten_helper(TreeNode* const node) {
        if (!node) {
            return nullptr;
        }

        auto* prev = flatten_helper(node->left);
        if (prev) {
            prev->right = node->right;
            node->right = node->left;
            node->left  = nullptr;
        }

        prev = flatten_helper(node->right);
        return prev ? prev : node;
    }

public:
    void flatten(TreeNode* root) { flatten_helper(root); }
};

}  // namespace recursive_v4

namespace recursive_v5 {

class Solution {
private:
    void flatten_helper(TreeNode*& node) {
        auto* curr = node;
        if (node->left) {
            node = node->left;
            flatten_helper(node);

            node->right = curr->right;
            curr->right = curr->left;
            curr->left  = nullptr;
        }

        if (node->right) {
            node = node->right;
            flatten_helper(node);
        }
    }

public:
    void flatten(TreeNode* root) {
        if (!root) {
            return;
        }

        auto* node = root;
        flatten_helper(node);
    }
};

}  // namespace recursive_v5

namespace recursive_v6 {

class Solution {
private:
    void flatten_helper(TreeNode* const node, TreeNode* next = nullptr) {
        if (node->right) {
            flatten_helper(node->right, next);
            next = node->right;
        }

        if (node->left) {
            flatten_helper(node->left, next);
            next = node->left;
        }

        node->right = next;
        node->left  = nullptr;
    }

public:
    void flatten(TreeNode* root) {
        if (!root) {
            return;
        }
        flatten_helper(root);
    }
};

}  // namespace recursive_v6

}  // anonymous namespace
