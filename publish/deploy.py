import os
import shutil
import subprocess
import sys       # <--- 确保导入了 sys
import json
import frontmatter

# =======================================================
# 👇【新增】加入这行代码，强制让 Python 输出 UTF-8，解决 emoji 报错
sys.stdout.reconfigure(encoding='utf-8')
# =======================================================

# ================= ⚙️ 配置区域 =================

# 1. 私有仓库（源）
PRIVATE_VAULT_PATH = r"D:\obsidian-gitsync\workspace"

# 2. 公开仓库（目标）
PUBLISH_REPO_PATH = r"D:\obsidian-gitsync\publish"

# 3. 文章子目录
TARGET_SUBDIR = "publish"

# 4. 记录同步状态的清单文件（存放在 Publish 仓库根目录，不会被发布）
MANIFEST_FILE = ".sync_manifest.json"

# ===============================================

def is_public(file_path):
    """读取文件 YAML Header"""
    try:
        post = frontmatter.load(file_path)
        return post.get('public') is True
    except Exception:
        return False

def load_manifest():
    """读取上次同步的文件列表"""
    manifest_path = os.path.join(PUBLISH_REPO_PATH, MANIFEST_FILE)
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_manifest(file_list):
    """保存本次同步的文件列表"""
    manifest_path = os.path.join(PUBLISH_REPO_PATH, MANIFEST_FILE)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(list(file_list), f, indent=2, ensure_ascii=False)

def sync_files_safely():
    dest_base_dir = os.path.join(PUBLISH_REPO_PATH, TARGET_SUBDIR)
    
    # 1. 获取当前所有需要同步的文件 (Current State)
    # 存储的是相对于 TARGET_SUBDIR 的路径
    current_sync_files = set()
    
    print("📥 扫描私有仓库中标记为 Public 的文件...")
    
    # 临时字典用于存储源文件路径，方便后续复制
    # Key: 相对路径, Value: 绝对源路径
    files_to_copy = {}

    for root, dirs, files in os.walk(PRIVATE_VAULT_PATH):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith(".md"):
                source_abs_path = os.path.join(root, file)
                if is_public(source_abs_path):
                    # 计算相对结构路径
                    rel_path = os.path.relpath(source_abs_path, PRIVATE_VAULT_PATH)
                    current_sync_files.add(rel_path)
                    files_to_copy[rel_path] = source_abs_path

    # 2. 读取上次的清单 (Previous State)
    previous_sync_files = load_manifest()

    # 3. 计算需要删除的文件 (上次有，这次没有的)
    files_to_delete = previous_sync_files - current_sync_files
    
    # 4. 执行删除 (只删除脚本自己产生过的旧文件)
    if files_to_delete:
        print(f"🧹 检测到 {len(files_to_delete)} 个文件需要被移除...")
        for rel_path in files_to_delete:
            full_path_to_delete = os.path.join(dest_base_dir, rel_path)
            if os.path.exists(full_path_to_delete):
                try:
                    os.remove(full_path_to_delete)
                    print(f"   ❌ 已移除旧文件: {rel_path}")
                except OSError as e:
                    print(f"   ⚠️ 移除失败: {rel_path}, {e}")
            
            # 尝试清理空文件夹 (可选)
            # 如果删除了文件导致文件夹为空，顺手删掉文件夹
            parent_dir = os.path.dirname(full_path_to_delete)
            if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                try:
                    os.rmdir(parent_dir)
                    print(f"   📂 移除空目录: {parent_dir}")
                except:
                    pass

    # 5. 执行复制/更新 (覆盖写入)
    print(f"🚀 开始同步 {len(current_sync_files)} 个文件...")
    for rel_path, src_path in files_to_copy.items():
        dest_path = os.path.join(dest_base_dir, rel_path)
        
        # 确保目标目录存在
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # 复制文件
        shutil.copy2(src_path, dest_path)
        # print(f"   ✅ 同步: {rel_path}") # 日志太长可以注释掉

    # 6. 保存新的清单
    save_manifest(current_sync_files)
    print("💾 同步清单已更新。")
    
    return len(current_sync_files) + len(files_to_delete)

def git_push():
    # ... (Git 推送部分代码保持不变) ...
    print("\n🚀 正在检查 Git 状态...")
    os.chdir(PUBLISH_REPO_PATH)
    try:
        subprocess.run(["git", "add", "."], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        if not status.stdout.strip():
            print("☕️ 内容无变化，无需推送。")
            return
        subprocess.run(["git", "commit", "-m", "Auto deploy from Private Vault"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("🌟 发布成功！")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git 操作出错: {e}")

if __name__ == "__main__":
    if sync_files_safely() > 0:
        git_push()
    else:
        # 即使没有文件变动，如果有文件被删除了，sync_files_safely 也会返回 > 0
        # 只有在完全没有任何 Public 文件且没有删除操作时，才会到这里
        print("🔍 扫描完毕，未检测到变动。")