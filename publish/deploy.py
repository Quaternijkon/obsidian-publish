import os
import shutil
import sys
import json
import frontmatter  # pip install python-frontmatter

# ================= ⚙️ 配置区域 =================

# 1. 私有仓库（源）
PRIVATE_VAULT_PATH = r"D:\obsidian-gitsync\source"

# 2. 公开仓库（目标）
PUBLISH_REPO_PATH = r"D:\obsidian-gitsync\publish\publish"

# 3. 文章子目录 (mdbook 填 "src", Hugo/Hexo 填 "content")
TARGET_SUBDIR = "src"

# 4. 记录同步状态的清单文件
MANIFEST_FILE = ".sync_manifest.json"

# ===============================================

# 防止 Windows 控制台因为编码问题报错
sys.stdout.reconfigure(encoding='utf-8')

def is_public(file_path):
    """检查是否有 public: true"""
    try:
        post = frontmatter.load(file_path)
        return post.get('public') is True
    except Exception:
        return False

def load_manifest():
    """读取上次同步的清单"""
    manifest_path = os.path.join(PUBLISH_REPO_PATH, MANIFEST_FILE)
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_manifest(file_list):
    """保存本次同步的清单"""
    manifest_path = os.path.join(PUBLISH_REPO_PATH, MANIFEST_FILE)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(list(file_list), f, indent=2, ensure_ascii=False)

def sync_files_only():
    dest_base_dir = os.path.join(PUBLISH_REPO_PATH, TARGET_SUBDIR)
    
    # 1. 扫描当前需要公开的文件
    current_sync_files = set()
    print("[INFO] Scanning private vault for public files...")
    
    files_to_copy = {} # 暂存复制列表

    for root, dirs, files in os.walk(PRIVATE_VAULT_PATH):
        # 忽略隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith(".md"):
                source_abs_path = os.path.join(root, file)
                if is_public(source_abs_path):
                    # 计算相对路径
                    rel_path = os.path.relpath(source_abs_path, PRIVATE_VAULT_PATH)
                    current_sync_files.add(rel_path)
                    files_to_copy[rel_path] = source_abs_path

    # 2. 读取旧清单，找出需要删除的文件
    previous_sync_files = load_manifest()
    files_to_delete = previous_sync_files - current_sync_files
    
    # 3. 执行删除
    if files_to_delete:
        print(f"[CLEAN] Removing {len(files_to_delete)} old files...")
        for rel_path in files_to_delete:
            full_path_to_delete = os.path.join(dest_base_dir, rel_path)
            if os.path.exists(full_path_to_delete):
                try:
                    os.remove(full_path_to_delete)
                    print(f"   - Removed: {rel_path}")
                except OSError as e:
                    print(f"   ! Error removing: {rel_path}, {e}")
            
            # 尝试清理空文件夹
            parent_dir = os.path.dirname(full_path_to_delete)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                except:
                    pass

    # 4. 执行复制/更新
    if current_sync_files:
        print(f"[SYNC] Copying {len(current_sync_files)} files...")
        for rel_path, src_path in files_to_copy.items():
            dest_path = os.path.join(dest_base_dir, rel_path)
            
            # 确保目录存在
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
            # 复制文件
            shutil.copy2(src_path, dest_path)
            # print(f"   + Copied: {rel_path}") # 如果文件太多，可以注释掉这行

    # 5. 更新清单
    save_manifest(current_sync_files)
    print(f"[DONE] Synchronization complete. Manifest updated.")

if __name__ == "__main__":
    sync_files_only()