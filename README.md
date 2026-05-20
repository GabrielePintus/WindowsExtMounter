# WSL Ext4 Partition Mounter

⚠️ Disclaimer: this code is 100% vibecoded and completely unreviewed (for now).

A graphical user interface (GUI) application for Windows that simplifies mounting and unmounting ext4 partitions using WSL2. No more typing complex PowerShell commands!

![WSL Mounter](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 🖱️ **Easy-to-use GUI** - No command line knowledge required
- 🔍 **Auto-detection** - Automatically scans and lists all physical disks
- 🐧 **WSL Distro Detection** - Automatically detects installed WSL distributions
- 📊 **Partition viewer** - Shows all partitions on selected disks
- 🗂️ **Multiple filesystems** - Supports ext4, ext3, ext2, btrfs, xfs
- 📝 **Activity logging** - Real-time status updates and error messages
- 📂 **Auto-open mounted location** - Automatically opens File Explorer to mounted partition
- ⚡ **Quick unmount** - Unmount all disks with one click

## Prerequisites

### System Requirements
- **Windows 11** or **Windows 10** (version 2004 or higher)
- **WSL2** installed and configured
- At least one WSL distribution (Ubuntu, Debian, etc.)
- **Administrator privileges**

### Check WSL Version
Open PowerShell and run:
```powershell
wsl --version
```

If WSL is not installed or you're on WSL1, update with:
```powershell
wsl --update
wsl --set-default-version 2
```

### Python Requirements
- Python 3.8 or higher
- PyQt6

## Installation

### Step 1: Install Python Dependencies

```bash
pip install PyQt6
```

Or using the requirements file:
```bash
pip install -r requirements.txt
```

### Step 2: Download the Application

Save `wsl_ext4_mounter.py` to your preferred directory.

### Step 3: Run as Administrator

**Important:** The application MUST be run with administrator privileges!

**Method 1 - Right-click:**
1. Right-click `wsl_ext4_mounter.py`
2. Select "Run as administrator"

**Method 2 - PowerShell:**
```powershell
# Navigate to the directory
cd C:\path\to\application

# Run with admin privileges
Start-Process python -ArgumentList "wsl_ext4_mounter.py" -Verb RunAs
```

**Method 3 - Create a shortcut:**
1. Right-click the `.py` file → Create shortcut
2. Right-click the shortcut → Properties
3. Click "Advanced..." → Check "Run as administrator"
4. Use the shortcut to launch

## Usage

### Basic Workflow

1. **Launch the application** (as Administrator)
2. **WSL Distributions detected** - The app automatically finds your installed WSL distros
3. **Click "Scan Disks"** - The application will detect all physical disks
4. **Select a disk** from the list
5. **Choose WSL distribution** from the dropdown (usually auto-selected to default)
6. **Choose partition number** from the dropdown
7. **Select filesystem type** (usually ext4)
8. **Click "Mount Partition"**
9. **Click "Yes"** to automatically open the mounted location in File Explorer
10. **Access your files!** The exact path is automatically determined and opened

### Finding Your Mounted Files

The application automatically:
- Detects your WSL distribution (Ubuntu, Debian, etc.)
- Determines the exact mount point (usually `/mnt/wsl/PHYSICALDRIVE...`)
- Constructs the Windows network path
- Opens it directly in File Explorer

You can also manually navigate to:
- **Network path:** `\\wsl$\<YourDistro>\mnt\wsl\`
- **Or use:** `\\wsl.localhost\<YourDistro>\mnt\wsl\`

From within WSL terminal:
```bash
cd /mnt/wsl
ls
```

### Additional Features

- **Open Last Mount** button: Re-open the last mounted location without re-mounting
- **Refresh Distros** button: Refresh the list of WSL distributions if you install a new one
- **Auto-path detection**: No need to manually type paths anymore!

### Unmounting

Click **"Unmount All"** when you're done to safely detach all mounted disks.

## Important Limitations

### ⚠️ Known Restrictions (from Microsoft documentation)

1. **Cannot mount Windows system disk**
   - You cannot mount partitions on the same physical disk where Windows is installed
   - This is a security limitation by Microsoft
   - For dual-boot setups on the same disk, you'll need alternative methods

2. **Entire disk attachment**
   - WSL2 attaches the entire physical disk, not just the partition
   - Even when mounting one partition, the whole disk becomes unavailable to Windows

3. **USB device limitations**
   - USB flash drives and SD cards may not work reliably
   - External USB hard drives generally work well
   - For USB devices, you may need `usbipd` tool

4. **Partition must not be in use**
   - Disks currently mounted in Windows cannot be mounted
   - Safely eject from Windows before mounting in WSL

## Supported Filesystems

- **ext4** (recommended for Linux partitions)
- **ext3**
- **ext2**
- **btrfs**
- **xfs**

## Troubleshooting

### "Access Denied" or Permission Errors
- **Solution:** Run the application as Administrator
- Right-click and select "Run as administrator"

### "Failed to mount with error code: -1"
- **Cause:** Disk is on the same physical drive as Windows
- **Solution:** This is a Microsoft limitation - use external drives only

### "WSL is not installed" or "Command not found"
```powershell
# Install WSL
wsl --install

# Or update existing WSL
wsl --update
```

### Disk not appearing in list
- Refresh Windows by unplugging and replugging the drive
- Check if the disk is initialized in Disk Management
- Ensure the drive is not encrypted

### Cannot find mounted files
1. Check which distributions are installed:
   ```powershell
   wsl --list
   ```
2. The application should automatically detect and select the correct distribution
3. If detection fails, use the refresh button (🔄) next to the distro dropdown
4. Try manually navigating to `\\wsl$\` in File Explorer to see available distributions

### "No WSL distributions found"
```powershell
# Install a WSL distribution
wsl --install -d Ubuntu

# Or list available distributions
wsl --list --online
```

### "The system cannot find the path specified"
- Start your WSL distribution first:
  ```powershell
  wsl -d Ubuntu
  ```
- Then try accessing `\\wsl$\Ubuntu\mnt\wsl\`

## Command Line Equivalents

If you prefer the command line, here are the equivalent commands:

### List disks:
```powershell
Get-CimInstance -Query "SELECT * from Win32_DiskDrive"
```

### Mount a partition:
```powershell
wsl --mount \\.\PHYSICALDRIVE2 --partition 1 --type ext4
```

### Unmount all:
```powershell
wsl --unmount
```

## Advanced Usage

### Manual mounting within WSL
If auto-mount fails, you can manually mount:

```bash
# Inside WSL, list block devices
lsblk

# Mount manually
sudo mkdir -p /mnt/mydisk
sudo mount /dev/sdc1 /mnt/mydisk
```

### Mount with specific options
The GUI currently doesn't support mount options, but you can use:

```powershell
wsl --mount \\.\PHYSICALDRIVE2 --partition 1 --type ext4 --options "ro"
```

## Security Considerations

- **Administrator access required:** This is by design - mounting disks requires elevated privileges
- **Data safety:** Always unmount properly before removing drives
- **Read-only mode:** Consider mounting in read-only mode for safety:
  - Use command line with `--options "ro"`

## Technical Details

### How it works
The application uses:
1. **PowerShell** - To query disk information via `Win32_DiskDrive`
2. **diskpart** - To list partitions on each disk
3. **WSL2** - To mount the partition using `wsl --mount` command
4. **PyQt6** - For the graphical interface

### Architecture
```
Windows (Admin) → PowerShell/diskpart → WSL2 → Linux Kernel → Mounted filesystem
```

## Alternative Methods

If WSL mounting doesn't work for your use case:

1. **Ext2Fsd** (older, but works): https://github.com/bobranten/Ext4Fsd
   - Can mount ext4 directly in Windows
   - Useful for same-disk dual-boot scenarios

2. **WSL + usbipd** for USB devices:
   - Install usbipd: `winget install usbipd`
   - Attach USB devices to WSL

3. **Virtual machine** (VirtualBox, VMware)
   - Mount the drive in a Linux VM
   - Share files via network

## Contributing

Contributions are welcome! Some ideas:
- Add support for mount options (read-only, noatime, etc.)
- Implement custom mount point names
- Add disk health information
- Support for VHD/VHDX files
- Remember previous mount configurations

## License

MIT License - Feel free to modify and distribute

## Acknowledgments

- Microsoft WSL Team for the `wsl --mount` feature
- PyQt6 for the GUI framework
- The Linux kernel maintainers for ext4 support

## Resources

- [Microsoft WSL Documentation](https://learn.microsoft.com/en-us/windows/wsl/)
- [WSL Disk Mounting Guide](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)

## Version History

- **v1.1** (2025) - Enhanced version
  - Auto-detection of WSL distributions
  - Automatic mount path discovery
  - One-click open in File Explorer
  - "Open Last Mount" feature
  - Refresh distros button
  
- **v1.0** (2025) - Initial release
  - Disk scanning
  - Partition mounting/unmounting
  - Multi-filesystem support
  - Activity logging

