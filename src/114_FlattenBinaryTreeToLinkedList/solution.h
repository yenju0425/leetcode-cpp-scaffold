#include <util/leetcode.h>

namespace default_ {

using namespace std;
using namespace util;

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

}  // namespace default_
