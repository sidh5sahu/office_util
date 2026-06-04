import os
import hashlib
import shutil

def bulk_rename(file_list, prefix="", suffix="", replace_src=None, replace_dest=None):
    renamed_count = 0
    for file_path in file_list:
        if not os.path.exists(file_path): continue
        
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        new_name = name
        
        # Replacements
        if replace_src and replace_dest is not None:
            new_name = new_name.replace(replace_src, replace_dest)
            
        # Prefix/Suffix
        new_name = f"{prefix}{new_name}{suffix}"
        
        new_filename = f"{new_name}{ext}"
        new_path = os.path.join(directory, new_filename)
        
        try:
            os.rename(file_path, new_path)
            renamed_count += 1
        except Exception:
            pass
    return renamed_count

def calculate_hash(file_path, algo="md5"):
    hash_func = None
    if algo == "md5": hash_func = hashlib.md5()
    elif algo == "sha256": hash_func = hashlib.sha256()
    elif algo == "sha1": hash_func = hashlib.sha1()
    
    if not hash_func: return "Invalid Algorithm"
    
    with open(file_path, "rb") as f:
        # Read in chunks
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
            
    return hash_func.hexdigest()

def get_dir_size(path):
    total = 0
    for entry in os.scandir(path):
        if entry.is_file():
            total += entry.stat().st_size
        elif entry.is_dir():
            total += get_dir_size(entry.path)
    return total

def organize_folder(folder_path):
    # Moves files into folders based on extension
    moved = 0
    if not os.path.isdir(folder_path): return 0
    
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        if os.path.isfile(item_path):
            ext = os.path.splitext(item)[1].lower().replace('.', '')
            if not ext: ext = "others"
            
            target_dir = os.path.join(folder_path, ext)
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            shutil.move(item_path, os.path.join(target_dir, item))
            moved += 1
    return moved

def find_duplicates(folder_path):
    """Find duplicate files in a folder by comparing MD5 hashes.
    Returns a dict with hash as key and list of file paths as value."""
    hash_map = {}
    duplicates = {}
    
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                file_hash = calculate_hash(file_path, "md5")
                if file_hash in hash_map:
                    if file_hash not in duplicates:
                        duplicates[file_hash] = [hash_map[file_hash]]
                    duplicates[file_hash].append(file_path)
                else:
                    hash_map[file_hash] = file_path
            except:
                pass
    
    return duplicates

def clean_empty_folders(folder_path):
    """Remove all empty directories within a folder. Returns count of deleted folders."""
    deleted_count = 0
    
    # Walk bottom-up so we delete empty subdirectories first
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            try:
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    deleted_count += 1
            except:
                pass
    
    return deleted_count


def base64_encode(input_path, output_path):
    """Encode a file to base64 text."""
    import base64
    with open(input_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode("utf-8")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(encoded)
    print(f"Base64 encoded: {len(data)} bytes -> {len(encoded)} chars")


def base64_decode(input_path, output_path):
    """Decode a base64 text file back to binary."""
    import base64
    with open(input_path, "r", encoding="utf-8") as f:
        encoded = f.read().strip()
    data = base64.b64decode(encoded)
    with open(output_path, "wb") as f:
        f.write(data)
    print(f"Base64 decoded: {len(encoded)} chars -> {len(data)} bytes")


def get_disk_usage(path):
    """Get disk usage information for a path. Returns dict with space info and extension breakdown."""
    total, used, free = shutil.disk_usage(path)
    
    # Extension breakdown
    ext_sizes = {}
    file_count = 0
    for root, dirs, files in os.walk(path):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                size = os.path.getsize(file_path)
                ext = os.path.splitext(filename)[1].lower() or "(no ext)"
                ext_sizes[ext] = ext_sizes.get(ext, 0) + size
                file_count += 1
            except (OSError, PermissionError):
                pass

    # Sort by size descending
    sorted_exts = sorted(ext_sizes.items(), key=lambda x: x[1], reverse=True)

    return {
        "total": total,
        "used": used,
        "free": free,
        "file_count": file_count,
        "extensions": sorted_exts,
    }


def format_size(size_bytes):
    """Format bytes into human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"
