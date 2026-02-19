# 🌳 Binary Tree Reconstruction Cheatsheet

## ✅ When Reconstruction Is Unique (node values must be unique)

| Traversals | Unique? |
|------------|----------|
| Inorder + Preorder | ✅ Yes |
| Inorder + Postorder | ✅ Yes |
| Preorder + Postorder | ❌ No (unless Full Binary Tree) |

---

## 🔑 Core Rules

### Inorder + Preorder
- `preorder[0]` = **root**
- Find root in inorder
- Split inorder into:
  - left subtree
  - right subtree
- Recurse on subtrees

> Preorder gives root **first**

---

### Inorder + Postorder
- `postorder[n-1]` = **root**
- Find root in inorder
- Split inorder into:
  - left subtree
  - right subtree
- Recurse on subtrees

> Postorder gives root **last**

---

## 🧠 Traversal Patterns

- Inorder = [ left | root | right ]
- Preorder = [ root | left | right ]
- Postorder = [ left | right | root ]


👉 Inorder splits the tree  
👉 Pre/Post identifies the root  

---

## ⚡ Optimization

- Build a hashmap: `value → inorder index`
- Avoid repeated searching
- Time Complexity: O(n)
- Space Complexity: O(n)

---

## ❗ Common Pitfalls

- Node values must be **unique**
- Be careful with index ranges
- Preorder + Postorder alone is **ambiguous**

---

## 🎯 One-Line Summary

Inorder splits the tree.  
Preorder/Postorder tells you where the root is.
