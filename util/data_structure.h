#ifndef UTIL_DATA_STRUCTURE_H
#define UTIL_DATA_STRUCTURE_H

#include <boost/json.hpp>

namespace util {

struct TreeNode {
    int val;
    TreeNode* left;
    TreeNode* right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode* left, TreeNode* right) : val(x), left(left), right(right) {}
};

TreeNode* build_tree_level_order(const boost::json::value& val);
boost::json::value dump_tree_level_order(TreeNode* root);

}  // namespace util

#endif /* UTIL_DATA_STRUCTURE_H */
