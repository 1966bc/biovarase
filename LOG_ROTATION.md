# Log Rotation - Biovarase

**Implementato:** 2025-12-03
**File:** `frames/login.py`

---

## 📋 Overview

Sistema di log rotation automatico per prevenire crescita illimitata di `log.txt`.

### Funzionalità

1. **Automatic rotation** quando log.txt supera 10 MB
2. **Old log cleanup** mantiene solo gli ultimi 5 file rotati
3. **Fail-safe** non causa mai crash dell'applicazione
4. **Zero configuration** funziona out-of-the-box

---

## ⚙️ Configurazione

### Costanti (frames/login.py righe 62-63)

```python
LOG_MAX_SIZE_MB = 10  # Maximum log file size before rotation
LOG_KEEP_COUNT = 5    # Number of old log files to keep
```

**Per modificare:**
1. Apri `frames/login.py`
2. Cambia i valori delle costanti
3. Riavvia l'applicazione

**Valori consigliati:**
- **Desktop single-user:** 10 MB, 5 file (default)
- **Server multi-user:** 50 MB, 10 file
- **Development:** 5 MB, 3 file

---

## 🔄 Come funziona

### Workflow

```
Application start
      ↓
main() chiamata
      ↓
rotate_log_if_needed()
      ↓
log.txt > 10 MB?
      ↓
    YES → Rename to log_YYYYMMDD_HHMMSS.txt
      ↓
cleanup_old_logs()
      ↓
Keep only 5 most recent
      ↓
Delete old rotated logs
      ↓
Continue startup
```

### Naming Convention

```
log.txt                  ← Active log (current session)
log_20251203_090000.txt ← Rotated 2025-12-03 09:00:00
log_20251202_150000.txt ← Rotated 2025-12-02 15:00:00
log_20251201_120000.txt ← Older...
log_20251130_180000.txt
log_20251129_100000.txt ← Oldest kept (5th)
(older files deleted automatically)
```

### Timing

**Rotation check happens:**
- ✅ Every application start (before any logging)
- ❌ NOT during runtime (only at startup)

**Why at startup only?**
- Desktop app (restart common)
- Prevents I/O overhead during operation
- Simpler implementation
- Sufficient for typical usage

---

## 📊 Disk Space Usage

### Calculation

```
Max disk space = (LOG_MAX_SIZE_MB × LOG_KEEP_COUNT) + LOG_MAX_SIZE_MB
               = (10 MB × 5) + 10 MB
               = 60 MB maximum
```

**Examples:**

| Config | Max Space |
|--------|-----------|
| 10 MB, 5 files | 60 MB |
| 50 MB, 10 files | 550 MB |
| 5 MB, 3 files | 20 MB |

---

## 🧪 Testing

### Test Script

```bash
cd /home/bc/Documents/projects/biovarase
./test_log_rotation.py
```

**Tests performed:**
1. Rotation when log > 10 MB
2. No rotation when log < 10 MB
3. Cleanup keeps only 5 old logs

### Manual Testing

```bash
# 1. Create large log
dd if=/dev/zero of=log.txt bs=1M count=15

# 2. Check size
ls -lh log.txt

# 3. Start application
./biovarase.py

# 4. Verify rotation happened
ls -lh log*.txt
```

---

## 🐛 Troubleshooting

### Issue: Log not rotating

**Check:**
```bash
# Is log.txt really > 10 MB?
ls -lh log.txt

# Permissions OK?
ls -l log.txt

# Any error messages on console?
./biovarase.py 2>&1 | grep -i log
```

**Solution:**
- Verify `LOG_MAX_SIZE_MB` value in login.py
- Check file permissions (need write access)
- Look for errors in console output

---

### Issue: Old logs not deleted

**Check:**
```bash
# How many old logs exist?
ls -1 log_*.txt | wc -l

# Are they really old?
ls -lt log_*.txt
```

**Solution:**
- Verify `LOG_KEEP_COUNT` value in login.py
- Check file permissions for deletion
- Manually delete if needed: `rm log_*.txt`

---

### Issue: Rotation failed error

**Console shows:**
```
[WARNING] Log rotation failed: [Errno 13] Permission denied
```

**Solution:**
```bash
# Check current user
whoami

# Check log.txt ownership
ls -l log.txt

# Fix permissions
chmod 644 log.txt
chown $USER:$USER log.txt
```

---

## 📝 Implementation Details

### Functions (frames/login.py)

#### `rotate_log_if_needed()`
**Location:** lines 133-173
**Called by:** `main()` at startup
**Purpose:** Check log size and rotate if needed

```python
def rotate_log_if_needed() -> None:
    """Rotate log.txt if > LOG_MAX_SIZE_MB"""
    if not os.path.exists("log.txt"):
        return

    size_mb = os.path.getsize("log.txt") / (1024 * 1024)

    if size_mb <= LOG_MAX_SIZE_MB:
        return  # Still small

    # Rotate
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    os.rename("log.txt", f"log_{timestamp}.txt")

    # Cleanup old logs
    cleanup_old_logs()
```

---

#### `cleanup_old_logs(keep)`
**Location:** lines 91-130
**Called by:** `rotate_log_if_needed()`
**Purpose:** Delete old rotated logs, keep only N most recent

```python
def cleanup_old_logs(keep: int = LOG_KEEP_COUNT) -> None:
    """Keep only N most recent rotated logs"""
    import glob

    log_files = glob.glob("log_*.txt")

    if len(log_files) <= keep:
        return  # Nothing to delete

    log_files.sort()  # Sort by timestamp (filename)
    to_delete = log_files[: len(log_files) - keep]

    for old_log in to_delete:
        os.remove(old_log)
```

---

## 🔒 Safety Features

### Fail-Safe Design

**All log functions are wrapped in try/except:**
```python
try:
    # Log operation
except Exception:
    pass  # Never crash the app due to logging
```

**Why?**
- Medical software - **reliability > logging**
- Logging issues must not prevent QC operations
- Graceful degradation

### Atomic Operations

**Rotation uses `os.rename()`:**
- Atomic operation (no partial files)
- Safe even if app crashes mid-rotation
- No data loss risk

---

## 📈 Future Enhancements

### Possible Improvements

1. **Runtime rotation** (not just startup)
   ```python
   # Check size after every N log writes
   if write_count % 100 == 0:
       rotate_log_if_needed()
   ```

2. **Compression** of old logs
   ```python
   import gzip
   with gzip.open(f"{old_log}.gz", "wb") as gz:
       with open(old_log, "rb") as f:
           gz.write(f.read())
   ```

3. **Time-based rotation** (daily/weekly)
   ```python
   # Rotate every day at midnight
   if last_rotation_date != today:
       rotate_log()
   ```

4. **Log level filtering** (keep only ERROR/WARNING in production)

5. **Remote log shipping** (to central server)

---

## 🎓 Best Practices

### For Developers

✅ **DO:**
- Use `log_to_file()` for startup messages
- Use `engine.on_log()` for exceptions after Engine created
- Test with `test_log_rotation.py` before deploy
- Document any config changes

❌ **DON'T:**
- Don't change rotation logic without testing
- Don't set LOG_MAX_SIZE_MB < 1 MB (too frequent rotation)
- Don't set LOG_KEEP_COUNT = 0 (lose all history)
- Don't delete log.txt manually during runtime

---

### For System Administrators

**Monitoring:**
```bash
# Check log size daily
watch -n 86400 ls -lh /path/to/biovarase/log*.txt

# Alert if total logs > 100 MB
du -sh /path/to/biovarase/log*.txt
```

**Backup:**
```bash
# Daily backup of rotated logs
0 2 * * * tar czf /backup/biovarase_logs_$(date +\%Y\%m\%d).tar.gz /path/to/biovarase/log_*.txt
```

**Manual cleanup:**
```bash
# If needed, manually delete old logs
cd /path/to/biovarase
rm log_2025*.txt  # Delete all old logs (keep log.txt)
```

---

## 📞 Support

**Issues with log rotation?**

1. Check this document first
2. Run `./test_log_rotation.py` to verify functionality
3. Check console output for error messages
4. Review `log.txt` for rotation messages
5. Check file permissions with `ls -l`

**Still not working?**
- Contact: giuseppecostanzi@gmail.com
- Include: OS version, Python version, error messages, `ls -lh log*.txt` output

---

## 📜 Change Log

### 2025-12-03 - Initial Implementation
- ✅ Automatic rotation at 10 MB
- ✅ Keep 5 old log files
- ✅ Fail-safe error handling
- ✅ Test suite created
- ✅ Documentation written

---

**Version:** 1.0
**Status:** Production Ready ✅
**Tested:** Linux (Debian 12), Windows 10/11
**Python:** 3.7+
