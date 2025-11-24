#!/usr/bin/env python3
"""
Test script for distributed storage system
Tests virtual disk, file system, and basic operations
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from storage.virtual_disk_manager import VirtualDiskManager
from storage.virtual_file_system import VirtualFileSystem
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_virtual_disk():
    """Test virtual disk creation"""
    print("\n" + "=" * 70)
    print("TEST 1: Virtual Disk Creation")
    print("=" * 70)
    
    # Create 1GB virtual disk
    disk_path = "test_storage/test_disk.img"
    disk_manager = VirtualDiskManager(disk_path, size_gb=1)
    
    # Create sparse disk
    disk_manager.create(sparse=True)
    
    print(f"✓ Virtual disk created: {disk_path}")
    print(f"✓ File exists: {Path(disk_path).exists()}")
    print(f"✓ File size: {Path(disk_path).stat().st_size:,} bytes")
    
    return disk_manager


def test_file_system(disk_manager):
    """Test file system operations"""
    print("\n" + "=" * 70)
    print("TEST 2: File System Operations")
    print("=" * 70)
    
    # Open disk
    disk_manager.open()
    
    # Create file system
    fs = VirtualFileSystem(disk_manager.disk_file)
    fs.format(disk_manager.size_bytes)
    
    print("✓ File system formatted")
    
    # Write test file
    test_data = b"Hello, Distributed Cloud Storage! " * 1000  # ~35KB
    inode_id = fs.write_file("/test/hello.txt", test_data)
    
    print(f"✓ File written (inode {inode_id}, {len(test_data):,} bytes)")
    
    # Read file back
    read_data = fs.read_file(inode_id)
    
    print(f"✓ File read ({len(read_data):,} bytes)")
    
    # Verify data
    assert read_data == test_data, "Data mismatch!"
    print("✓ Data verified (matches original)")
    
    # List files
    files = fs.list_files()
    print(f"✓ Files in system: {len(files)}")
    for file_info in files:
        print(f"  - {file_info['name']} ({file_info['size']:,} bytes, inode {file_info['inode_id']})")
    
    # Get stats
    stats = fs.get_stats()
    print(f"\n✓ File System Statistics:")
    print(f"  - Total blocks: {stats['total_blocks']:,}")
    print(f"  - Used blocks: {stats['used_blocks']:,}")
    print(f"  - Free blocks: {stats['free_blocks']:,}")
    print(f"  - Total size: {stats['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"  - Used size: {stats['used_size_bytes'] / (1024**2):.2f} MB")
    
    # Delete file
    fs.delete_file(inode_id)
    print(f"\n✓ File deleted (inode {inode_id})")
    
    # Verify deletion
    files = fs.list_files()
    print(f"✓ Files remaining: {len(files)}")
    
    disk_manager.close()
    
    return fs


def test_large_file():
    """Test with larger file"""
    print("\n" + "=" * 70)
    print("TEST 3: Large File Test")
    print("=" * 70)
    
    # Create 5GB virtual disk
    disk_path = "test_storage/large_disk.img"
    disk_manager = VirtualDiskManager(disk_path, size_gb=5)
    disk_manager.create(sparse=True)
    disk_manager.open()
    
    # Create file system
    fs = VirtualFileSystem(disk_manager.disk_file)
    fs.format(disk_manager.size_bytes)
    
    # Write 100MB file
    large_data = b"X" * (100 * 1024 * 1024)  # 100MB
    print(f"Writing {len(large_data) / (1024**2):.2f} MB file...")
    
    inode_id = fs.write_file("/data/large_file.bin", large_data)
    print(f"✓ Large file written (inode {inode_id})")
    
    # Read back
    print("Reading file back...")
    read_data = fs.read_file(inode_id)
    
    assert len(read_data) == len(large_data), "Size mismatch!"
    assert read_data == large_data, "Data mismatch!"
    print("✓ Large file verified")
    
    # Stats
    stats = fs.get_stats()
    print(f"✓ Used space: {stats['used_size_bytes'] / (1024**2):.2f} MB")
    
    disk_manager.close()


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("  DISTRIBUTED CLOUD STORAGE - SYSTEM TEST")
    print("=" * 70)
    
    try:
        # Test 1: Virtual disk
        disk_manager = test_virtual_disk()
        
        # Test 2: File system
        test_file_system(disk_manager)
        
        # Test 3: Large file
        test_large_file()
        
        print("\n" + "=" * 70)
        print("  ALL TESTS PASSED ✓")
        print("=" * 70)
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

