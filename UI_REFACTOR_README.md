# PwnSafe UI Refactor

## Overview

The PwnSafe UI has been refactored from a bloated cyberpunk interface to a compact, professional desktop utility. The new design follows modern UI principles with clean spacing, collapsible sections, and improved user experience.

## New File Structure

### Core Files
- `ui_refactor.py` - Main compact UI implementation
- `ui_components.py` - Reusable UI widgets
- `profile_manager.py` - Profile persistence and management
- `ssh_auth_enhanced.py` - Enhanced SSH authentication

### Modified Files
- `pwnsafe.py` - Updated to use new UI (business logic preserved)

## Key Features

### 1. Compact Layout
- **8px base spacing unit** for consistent layout
- **No scrollable container** - everything fits on screen
- **Professional dark theme** with reduced neon intensity
- **Responsive design** for 1280×720 and 1920×1080 resolutions

### 2. Profile Management
- **JSON-based profiles** stored in `~/.pwnsafe/profiles.json`
- **Encrypted sensitive data** (SSH key passphrases)
- **Profile switching** with dropdown
- **Persistent settings** (window geometry, last backup dir)

### 3. Enhanced Authentication
- **Password authentication** (existing)
- **SSH key authentication** with file selection
- **SSH agent support** (try agent first, fallback to file)
- **Multiple key formats** (RSA, Ed25519, ECDSA, DSS)
- **Passphrase support** for encrypted keys

### 4. Collapsible Sections
- **Advanced Settings** (collapsed by default)
  - Auto-detect Pwnagotchi toggle
  - Network adapter selection
  - DNS settings
- **System Log** (initially visible, expandable)
  - Copy All / Clear buttons
  - Color-coded messages
  - Auto-scroll to bottom

### 5. Improved User Experience
- **Status bar** showing connection state
- **Toast notifications** for success/error messages
- **Keyboard shortcuts** (Enter to backup, Escape to close dialogs)
- **Input validation** with helpful error messages
- **Restore button** disabled until file selected

## UI Components

### CollapsibleSection
```python
section = CollapsibleSection(parent, "TITLE", is_expanded=False)
section.add_widget(widget, **pack_options)
```

### StatusBar
```python
status_bar = StatusBar(parent)
status_bar.update_status("Connected to 10.0.0.2", "connected")
```

### ToastNotification
```python
toast = ToastNotification(parent)
toast.show_toast("Operation successful!", "success")
```

### CompactLogViewer
```python
log_viewer = CompactLogViewer(parent, initial_height=100)
log_viewer.log_message("System message", "INFO")
```

## Profile Data Structure

```json
{
  "profiles": {
    "Default": {
      "host": "10.0.0.2",
      "username": "pi",
      "auth_method": "password",
      "ssh_key_path": "",
      "ssh_key_passphrase": "",
      "use_ssh_agent": false,
      "dns_primary": "",
      "dns_secondary": "",
      "auto_detect": true,
      "network_adapter": ""
    }
  },
  "last_profile": "Default",
  "last_backup_dir": "",
  "window_geometry": "900x700+100+100"
}
```

## Usage

### Running the New UI
```bash
python pwnsafe.py
```

### Testing Components
```bash
python test_ui.py
```

## Layout Structure

1. **Header** (60px) - Title + Status bar
2. **Profile** (40px) - Profile dropdown + Save button
3. **Connection** (80px) - Host, User, Auth method, Credentials
4. **Backup File** (50px) - File selection
5. **Primary Actions** (80px) - Backup/Restore buttons
6. **Advanced Settings** (Collapsible) - Auto-detect, DNS, Network
7. **System Log** (Collapsible) - Log viewer with controls

## Keyboard Shortcuts

- **Enter** - Trigger backup when focus is in connection/backup fields
- **Escape** - Close dialogs, collapse sections

## Color Scheme

- **Primary**: #00aa00 (subtle green)
- **Secondary**: #4488ff (blue)
- **Accent**: #ff6600 (orange)
- **Danger**: #cc0044 (red)
- **Warning**: #ffaa00 (yellow)
- **Background**: #1a1a1a (dark)
- **Surface**: #2a2a2a (surface)
- **Text**: #ffffff (white)
- **Muted**: #888888 (muted)

## Backward Compatibility

- All existing business logic functions preserved
- All menu bar items functional
- Existing backup files (.tgz) compatible
- SSH/backup/restore algorithms unchanged

## Future Enhancements

- Animated collapsible sections
- More SSH key format support
- Advanced network configuration
- Connection sharing features
- Profile import/export
