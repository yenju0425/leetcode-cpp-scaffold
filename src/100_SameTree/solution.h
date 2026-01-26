#include <util/leetcode.h>

namespace default_ {

using namespace std;

class Solution {
public:
    bool isSameTree(TreeNode* p, TreeNode* q) {
        return (!p && !q) ||
               (p && q && p->val == q->val && isSameTree(p->left, q->left) && isSameTree(p->right, q->right));
    }
};

}  // namespace default_
