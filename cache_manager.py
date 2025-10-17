"""
Cache management utilities with expiration and size limits
"""
import os
import time
import hashlib
from pathlib import Path
from typing import Optional
from logger import get_logger

logger = get_logger(__name__)

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Cache settings (in MB and days)
MAX_CACHE_SIZE_MB = 500
MAX_CACHE_AGE_DAYS = 30


def _key(url: str) -> str:
    """Generate a cache key from a URL.

    Args:
        url (str): The URL to generate a key for.

    Returns:
        str: The generated cache key.
    """
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]


def cache_path(url: str) -> Path:
    """Get the cache file path for a given URL.

    Args:
        url (str): The URL to get the cache path for.

    Returns:
        Path: The path to the cache file.
    """
    return CACHE_DIR / f"{_key(url)}.html"


def get_cache_size_mb() -> float:
    """Get the total size of the cache in megabytes.

    Returns:
        float: The total size of the cache in MB.
    """
    total_size = sum(f.stat().st_size for f in CACHE_DIR.glob("*.html") if f.is_file())
    return total_size / (1024 * 1024)


def get_cache_stats() -> dict:
    """Get statistics about the cache.

    Returns:
        dict: A dictionary containing cache statistics.
    """
    files = list(CACHE_DIR.glob("*.html"))
    total_size = sum(f.stat().st_size for f in files if f.is_file())

    return {
        "file_count": len(files),
        "total_size_mb": total_size / (1024 * 1024),
        "cache_dir": str(CACHE_DIR),
        "max_size_mb": MAX_CACHE_SIZE_MB,
        "max_age_days": MAX_CACHE_AGE_DAYS
    }


def is_cache_valid(url: str, max_age_days: int = MAX_CACHE_AGE_DAYS) -> bool:
    """Check if the cache for a given URL is valid and not expired.

    Args:
        url (str): The URL to check.
        max_age_days (int): The maximum age of a cache file in days.

    Returns:
        bool: True if the cache is valid, False otherwise.
    """
    path = cache_path(url)

    if not path.exists():
        return False

    # Check age
    file_age_days = (time.time() - path.stat().st_mtime) / (24 * 3600)
    if file_age_days > max_age_days:
        logger.debug(f"Cache expired for {url} (age: {file_age_days:.1f} days)")
        return False

    return True


def read_cache(url: str) -> Optional[str]:
    """Read the cached content for a given URL, if it is valid.

    Args:
        url (str): The URL to read from the cache.

    Returns:
        Optional[str]: The cached content, or None if the cache is not valid.
    """
    if not is_cache_valid(url):
        return None

    try:
        return cache_path(url).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"Error reading cache for {url}: {e}")
        return None


def write_cache(url: str, content: str) -> bool:
    """Write content to the cache for a given URL.

    Args:
        url (str): The URL to cache the content for.
        content (str): The HTML content to cache.

    Returns:
        bool: True if the write operation was successful, False otherwise.
    """
    try:
        cache_path(url).write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        logger.error(f"Error writing cache for {url}: {e}")
        return False


def cleanup_expired(max_age_days: int = MAX_CACHE_AGE_DAYS) -> int:
    """Remove expired files from the cache.

    Args:
        max_age_days (int): The maximum age of a cache file in days.

    Returns:
        int: The number of files that were deleted.
    """
    deleted = 0
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 3600

    for file_path in CACHE_DIR.glob("*.html"):
        try:
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                file_path.unlink()
                deleted += 1
                logger.debug(f"Deleted expired cache: {file_path.name}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

    logger.info(f"Cleaned up {deleted} expired cache files")
    return deleted


def cleanup_by_size(max_size_mb: float = MAX_CACHE_SIZE_MB) -> int:
    """Remove the oldest files from the cache if it exceeds the size limit.

    Args:
        max_size_mb (float): The maximum size of the cache in megabytes.

    Returns:
        int: The number of files that were deleted.
    """
    deleted = 0
    current_size = get_cache_size_mb()

    if current_size <= max_size_mb:
        return 0

    # Get files sorted by modification time (oldest first)
    files = sorted(
        CACHE_DIR.glob("*.html"),
        key=lambda f: f.stat().st_mtime
    )

    for file_path in files:
        if current_size <= max_size_mb:
            break

        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            file_path.unlink()
            current_size -= file_size_mb
            deleted += 1
            logger.debug(f"Deleted old cache: {file_path.name}")
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

    logger.info(f"Cleaned up {deleted} files to reduce cache size")
    return deleted


def cleanup_cache(max_age_days: int = MAX_CACHE_AGE_DAYS, max_size_mb: float = MAX_CACHE_SIZE_MB) -> dict:
    """Perform a full cache cleanup.

    This function removes expired files and enforces the cache size limit.

    Args:
        max_age_days (int): The maximum age of a cache file in days.
        max_size_mb (float): The maximum size of the cache in megabytes.

    Returns:
        dict: A dictionary containing cleanup statistics.
    """
    expired_deleted = cleanup_expired(max_age_days)
    size_deleted = cleanup_by_size(max_size_mb)

    stats = get_cache_stats()
    stats["expired_deleted"] = expired_deleted
    stats["size_deleted"] = size_deleted

    return stats


def clear_all_cache() -> int:
    """Delete all files from the cache.

    Returns:
        int: The number of files that were deleted.
    """
    deleted = 0
    for file_path in CACHE_DIR.glob("*.html"):
        try:
            file_path.unlink()
            deleted += 1
        except Exception as e:
            logger.error(f"Error deleting {file_path}: {e}")

    logger.info(f"Cleared all cache: {deleted} files deleted")
    return deleted
