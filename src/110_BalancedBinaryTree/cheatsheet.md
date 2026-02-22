# 🌳 Binary Tree Cheatsheet

## 📖 Core Terms

- **Node**: An element in the tree (often has `value`, `left`, `right`).
- **Edge**: A connection between a parent and a child.
- **Root**: The top node (has no parent).
- **Parent / Child**: Directly connected nodes (one level up / down).
- **Sibling**: Nodes that share the same parent.
- **Leaf**: A node with no children (`left == null && right == null`).
- **Subtree**: A node plus all its descendants.
- **Empty tree**: `root == null`.

---

## 🏗️ Structural Definitions

- **Binary Tree**: Each node has at most 2 children (`left`, `right`).
- **Binary Search Tree (BST)**: For every node:
  - All values in **left** subtree `< node.val`
  - All values in **right** subtree `> node.val`
  - (handling of equal values depends on the chosen convention)
- **Complete Binary Tree**: All levels are full except possibly the last; last level filled **left to right**.
- **Perfect Binary Tree**: Every level is full (all internal nodes have 2 children; all leaves at the same depth).
- **Full / Strict Binary Tree**: Each node has either **0 or 2** children (never exactly 1).
- **Balanced (Height-Balanced) Binary Tree**: For every node:
  - `|height(left) - height(right)| <= 1`

---

## 📏 Depth / Level / Height

> Pick one convention and stick to it.

- **Depth**: Distance from the **root** down to a node (in edges or nodes).
- **Level**: Same as depth; root is level 0 (or level 1, depending on convention).
- **Height**: Longest distance from a **node** down to a leaf.
  - Common (count nodes):  `height(null) = 0`, `height(leaf) = 1`
  - Alternative (count edges): `height(null) = -1`, `height(leaf) = 0`

---

## 🧠 Traversal Patterns

```
Preorder  (NLR) = [ root | left | right ]   — root first
Inorder   (LNR) = [ left | root | right ]   — BST inorder gives sorted order
Postorder (LRN) = [ left | right | root ]   — root last
Level-order (BFS)                           — level by level, using a queue
```

---

## ⚡ Quick Facts

- **Max nodes at level k**: $2^k$ (if root is level 0)
- **Max nodes in a perfect tree of height h**: $2^h - 1$ (if `height(leaf) = 1`)

---

## 🎯 One-Line Summary

Depth goes **down from root**.  
Height goes **up from leaf**.
