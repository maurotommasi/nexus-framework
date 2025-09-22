import os

def print_tree(start_path, prefix=""):
    items = sorted(os.listdir(start_path))
    for index, item in enumerate(items):
        path = os.path.join(start_path, item)
        connector = "└── " if index == len(items) - 1 else "├── "
        print(prefix + connector + item)
        if os.path.isdir(path):
            extension = "    " if index == len(items) - 1 else "│   "
            print_tree(path, prefix + extension)

if __name__ == "__main__":
    root_dir = os.path.dirname(__file__)  # project root
    print(os.path.basename(root_dir) or root_dir)
    print_tree(root_dir)
