import os

def generate_tree(dir_path: str, prefix: str = "") -> str:
    entries = sorted(os.listdir(dir_path))
    entries = [e for e in entries if not e.startswith('.')]  # Bỏ qua file/folder ẩn
    tree_str = ""
    entries_count = len(entries)

    for index, entry in enumerate(entries):
        path = os.path.join(dir_path, entry)
        connector = "└── " if index == entries_count - 1 else "├── "
        tree_str += prefix + connector + entry + "\n"
        if os.path.isdir(path):
            extension = "    " if index == entries_count - 1 else "│   "
            tree_str += generate_tree(path, prefix + extension)

    return tree_str

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))
    tree_output = os.path.basename(root_dir) + "/\n"
    tree_output += generate_tree(root_dir)

    with open("Tree.txt", "w", encoding="utf-8") as f:
        f.write(tree_output)

    print("✅ Đã tạo file Tree.txt chứa cây thư mục theo định dạng chuẩn.")
