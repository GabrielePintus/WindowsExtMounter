"""
WSL Ext4 Partition Mounter - GUI Tool
Easily mount and unmount ext4 partitions on Windows using WSL2

Requirements:
- Windows 11 or Windows 10 with WSL2
- Administrator privileges
- PyQt6 (install with: pip install PyQt6)
"""

import sys
import subprocess
import re
import os
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QLabel, QMessageBox, QGroupBox,
    QListWidgetItem, QTextEdit, QComboBox, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QDesktopServices
from PyQt6.QtCore import QUrl


class DiskInfo:
    """Represents a physical disk and its partitions"""
    def __init__(self, device_id: str, model: str, size: int, index: int):
        self.device_id = device_id
        self.model = model
        self.size = size
        self.index = index
        self.partitions: List[Dict] = []
    
    def __str__(self):
        size_gb = self.size / (1024**3)
        return f"Disk {self.index}: {self.model} ({size_gb:.1f} GB)"


class DiskScanner(QThread):
    """Background thread for scanning disks"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            disks = self.get_physical_disks()
            self.finished.emit(disks)
        except Exception as e:
            self.error.emit(str(e))
    
    @staticmethod
    def get_wsl_distributions() -> List[Dict[str, str]]:
        """Get list of installed WSL distributions"""
        try:
            result = subprocess.run(
                ['wsl', '--list', '--verbose'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-16-le'  # WSL output is UTF-16 LE
            )
            
            if result.returncode != 0:
                return []
            
            distros = []
            lines = result.stdout.split('\n')
            
            for line in lines[1:]:  # Skip header
                line = line.strip()
                if not line:
                    continue
                
                # Remove special characters and parse
                line = line.replace('*', '').strip()
                parts = line.split()
                
                if len(parts) >= 3:
                    name = parts[0]
                    state = parts[1]
                    version = parts[2]
                    
                    distros.append({
                        'name': name,
                        'state': state,
                        'version': version,
                        'default': '*' in line
                    })
            
            return distros
        
        except Exception as e:
            print(f"Error getting WSL distributions: {e}")
            return []
    
    def get_physical_disks(self) -> List[DiskInfo]:
        """Get list of physical disks using PowerShell"""
        try:
            cmd = 'Get-CimInstance -Query "SELECT * from Win32_DiskDrive" | ConvertTo-Json'
            result = subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                raise Exception(f"Failed to get disk information: {result.stderr}")
            
            import json
            data = json.loads(result.stdout)
            
            # Handle single disk (not a list)
            if isinstance(data, dict):
                data = [data]
            
            disks = []
            for idx, disk in enumerate(data):
                device_id = disk.get('DeviceID', '')
                model = disk.get('Model', 'Unknown')
                size = int(disk.get('Size', 0))
                
                disk_info = DiskInfo(device_id, model, size, idx)
                disk_info.partitions = self.get_disk_partitions(device_id)
                disks.append(disk_info)
            
            return disks
        
        except subprocess.TimeoutExpired:
            raise Exception("Timeout while scanning disks")
        except Exception as e:
            raise Exception(f"Error scanning disks: {str(e)}")
    
    def get_disk_partitions(self, device_id: str) -> List[Dict]:
        """Get partitions for a specific disk using diskpart"""
        try:
            # Extract disk number from device_id
            match = re.search(r'PHYSICALDRIVE(\d+)', device_id)
            if not match:
                return []
            
            disk_num = match.group(1)
            
            # Create diskpart script
            script = f"select disk {disk_num}\nlist partition\n"
            
            result = subprocess.run(
                ['diskpart'],
                input=script,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return []
            
            partitions = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                # Look for partition lines (e.g., "  Partition 1    Primary       100 MB  1024 KB")
                if 'Partition' in line and not 'Partition ---' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            partition_num = int(parts[1])
                            partition_type = parts[2] if len(parts) > 2 else 'Unknown'
                            partitions.append({
                                'number': partition_num,
                                'type': partition_type
                            })
                        except (ValueError, IndexError):
                            continue
            
            return partitions
        
        except Exception:
            return []


class WSLMounter(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.disks: List[DiskInfo] = []
        self.mounted_disks: List[str] = []
        self.wsl_distros: List[Dict[str, str]] = []
        self.last_mount_path: Optional[str] = None
        self.init_ui()
        self.check_admin_privileges()
        self.detect_wsl_distros()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("WSL Ext4 Partition Mounter")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("WSL Ext4 Partition Mounter")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Info label
        info_text = QLabel(
            "Mount ext4 partitions from external drives or dual-boot setups.\n"
            "Note: Cannot mount partitions on the same disk as Windows installation."
        )
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_text)
        
        # Disk list group
        disk_group = QGroupBox("Available Disks")
        disk_layout = QVBoxLayout()
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Scan Disks")
        refresh_btn.clicked.connect(self.scan_disks)
        disk_layout.addWidget(refresh_btn)
        
        # Disk list
        self.disk_list = QListWidget()
        self.disk_list.itemClicked.connect(self.on_disk_selected)
        disk_layout.addWidget(self.disk_list)
        
        disk_group.setLayout(disk_layout)
        layout.addWidget(disk_group)
        
        # Partition details group
        partition_group = QGroupBox("Partition Details")
        partition_layout = QVBoxLayout()
        
        # WSL Distribution selector
        distro_layout = QHBoxLayout()
        distro_layout.addWidget(QLabel("WSL Distro:"))
        self.distro_combo = QComboBox()
        self.distro_combo.setToolTip("Select WSL distribution to use for mounting")
        distro_layout.addWidget(self.distro_combo)
        
        self.refresh_distro_btn = QPushButton("🔄")
        self.refresh_distro_btn.setMaximumWidth(40)
        self.refresh_distro_btn.setToolTip("Refresh distribution list")
        self.refresh_distro_btn.clicked.connect(self.detect_wsl_distros)
        distro_layout.addWidget(self.refresh_distro_btn)
        
        partition_layout.addLayout(distro_layout)
        
        # Partition selector
        partition_selector_layout = QHBoxLayout()
        partition_selector_layout.addWidget(QLabel("Partition:"))
        self.partition_combo = QComboBox()
        partition_selector_layout.addWidget(self.partition_combo)
        partition_layout.addLayout(partition_selector_layout)
        
        # Filesystem type selector
        fs_layout = QHBoxLayout()
        fs_layout.addWidget(QLabel("Filesystem:"))
        self.fs_combo = QComboBox()
        self.fs_combo.addItems(['ext4', 'ext3', 'ext2', 'btrfs', 'xfs'])
        fs_layout.addWidget(self.fs_combo)
        partition_layout.addLayout(fs_layout)
        
        # Mount/Unmount buttons
        button_layout = QHBoxLayout()
        
        self.mount_btn = QPushButton("📁 Mount Partition")
        self.mount_btn.clicked.connect(self.mount_partition)
        self.mount_btn.setEnabled(False)
        button_layout.addWidget(self.mount_btn)
        
        self.open_mount_btn = QPushButton("📂 Open Last Mount")
        self.open_mount_btn.clicked.connect(self.open_last_mount)
        self.open_mount_btn.setEnabled(False)
        self.open_mount_btn.setToolTip("Open the last mounted location in File Explorer")
        button_layout.addWidget(self.open_mount_btn)
        
        self.unmount_btn = QPushButton("⏏️ Unmount All")
        self.unmount_btn.clicked.connect(self.unmount_all)
        button_layout.addWidget(self.unmount_btn)
        
        partition_layout.addLayout(button_layout)
        partition_group.setLayout(partition_layout)
        layout.addWidget(partition_group)
        
        # Status/Log area
        log_group = QGroupBox("Status Log")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Instructions button
        help_btn = QPushButton("ℹ️ Show Instructions")
        help_btn.clicked.connect(self.show_instructions)
        layout.addWidget(help_btn)
        
        self.log("Application started. Click 'Scan Disks' to begin.")
    
    def check_admin_privileges(self):
        """Check if running with administrator privileges"""
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                self.log("⚠️ WARNING: Not running as Administrator. Mount operations will fail.")
                QMessageBox.warning(
                    self,
                    "Administrator Required",
                    "This application requires Administrator privileges to mount disks.\n"
                    "Please right-click the application and select 'Run as administrator'."
                )
        except Exception as e:
            self.log(f"Could not check admin privileges: {e}")
    
    def detect_wsl_distros(self):
        """Detect installed WSL distributions"""
        self.log("Detecting WSL distributions...")
        self.distro_combo.clear()
        
        try:
            self.wsl_distros = DiskScanner.get_wsl_distributions()
            
            if not self.wsl_distros:
                self.log("⚠️ No WSL distributions found. Please install a WSL distribution first.")
                self.distro_combo.addItem("No distributions found")
                return
            
            # Add distributions to combo box
            for distro in self.wsl_distros:
                display_name = distro['name']
                if distro['state'] != 'Running':
                    display_name += f" ({distro['state']})"
                if distro.get('default', False):
                    display_name += " [Default]"
                
                self.distro_combo.addItem(display_name, distro)
            
            self.log(f"✅ Found {len(self.wsl_distros)} WSL distribution(s)")
            
            # Select default distribution
            for idx, distro in enumerate(self.wsl_distros):
                if distro.get('default', False):
                    self.distro_combo.setCurrentIndex(idx)
                    break
        
        except Exception as e:
            self.log(f"❌ Error detecting WSL distributions: {e}")
            self.distro_combo.addItem("Error detecting distributions")
    
    def log(self, message: str):
        """Add message to log"""
        self.log_text.append(message)
        # Scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def scan_disks(self):
        """Scan for available disks"""
        self.log("Scanning for disks...")
        self.disk_list.clear()
        self.partition_combo.clear()
        self.mount_btn.setEnabled(False)
        
        # Start background scan
        self.scanner = DiskScanner()
        self.scanner.finished.connect(self.on_scan_finished)
        self.scanner.error.connect(self.on_scan_error)
        self.scanner.start()
    
    def on_scan_finished(self, disks: List[DiskInfo]):
        """Handle scan completion"""
        self.disks = disks
        self.log(f"Found {len(disks)} disk(s)")
        
        for disk in disks:
            item = QListWidgetItem(str(disk))
            item.setData(Qt.ItemDataRole.UserRole, disk)
            self.disk_list.addItem(item)
    
    def on_scan_error(self, error: str):
        """Handle scan error"""
        self.log(f"❌ Error scanning disks: {error}")
        QMessageBox.critical(self, "Scan Error", f"Failed to scan disks:\n{error}")
    
    def on_disk_selected(self, item: QListWidgetItem):
        """Handle disk selection"""
        disk: DiskInfo = item.data(Qt.ItemDataRole.UserRole)
        self.partition_combo.clear()
        
        if not disk.partitions:
            self.log(f"No partitions found on {disk.model}")
            self.partition_combo.addItem("No partitions detected")
            self.mount_btn.setEnabled(False)
            return
        
        for partition in disk.partitions:
            self.partition_combo.addItem(
                f"Partition {partition['number']} ({partition['type']})",
                partition
            )
        
        self.mount_btn.setEnabled(True)
        self.log(f"Selected: {disk.model} - {len(disk.partitions)} partition(s)")
    
    def mount_partition(self):
        """Mount the selected partition"""
        current_item = self.disk_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a disk first.")
            return
        
        disk: DiskInfo = current_item.data(Qt.ItemDataRole.UserRole)
        partition_data = self.partition_combo.currentData()
        
        if not partition_data:
            QMessageBox.warning(self, "No Partition", "Please select a partition.")
            return
        
        # Check if a distribution is selected
        distro_data = self.distro_combo.currentData()
        if not distro_data or not self.wsl_distros:
            QMessageBox.warning(
                self,
                "No WSL Distribution",
                "No WSL distribution found. Please install a WSL distribution first.\n\n"
                "Run: wsl --install"
            )
            return
        
        distro_name = distro_data['name']
        partition_num = partition_data['number']
        filesystem = self.fs_combo.currentText()
        
        # Confirm action
        reply = QMessageBox.question(
            self,
            "Confirm Mount",
            f"Mount partition {partition_num} on {disk.model} as {filesystem}?\n\n"
            f"Device: {disk.device_id}\n"
            f"Partition: {partition_num}\n"
            f"Filesystem: {filesystem}\n"
            f"WSL Distro: {distro_name}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        self.log(f"Mounting {disk.device_id} partition {partition_num} as {filesystem}...")
        
        try:
            # Build mount command
            cmd = [
                'wsl', '--mount',
                disk.device_id,
                '--partition', str(partition_num),
                '--type', filesystem
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log(f"✅ Successfully mounted!")
                self.mounted_disks.append(disk.device_id)
                
                # Get the mount path
                mount_path = self.get_mount_path(distro_name, disk, partition_num)
                
                if mount_path:
                    self.last_mount_path = mount_path
                    self.open_mount_btn.setEnabled(True)
                    self.log(f"Mount path: {mount_path}")
                    
                    # Ask user if they want to open the directory
                    reply = QMessageBox.question(
                        self,
                        "Mount Successful",
                        f"Partition mounted successfully!\n\n"
                        f"Mount location:\n{mount_path}\n\n"
                        f"Would you like to open this location in File Explorer?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.open_mount_location(mount_path)
                else:
                    self.log(f"Access at: \\\\wsl$\\{distro_name}\\mnt\\wsl\\...")
                    QMessageBox.information(
                        self,
                        "Mount Successful",
                        f"Partition mounted successfully!\n\n"
                        f"Access it in File Explorer at:\n"
                        f"\\\\wsl$\\{distro_name}\\mnt\\wsl\\"
                    )
            else:
                error_msg = result.stderr or result.stdout
                self.log(f"❌ Mount failed: {error_msg}")
                QMessageBox.critical(
                    self,
                    "Mount Failed",
                    f"Failed to mount partition:\n{error_msg}\n\n"
                    f"Common issues:\n"
                    f"- Not running as Administrator\n"
                    f"- Partition is on the same disk as Windows\n"
                    f"- Partition is already mounted\n"
                    f"- WSL2 is not properly installed"
                )
        
        except subprocess.TimeoutExpired:
            self.log("❌ Mount operation timed out")
            QMessageBox.critical(self, "Timeout", "Mount operation timed out.")
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")
    
    def unmount_all(self):
        """Unmount all mounted disks"""
        reply = QMessageBox.question(
            self,
            "Confirm Unmount",
            "Unmount all mounted disks?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        self.log("Unmounting all disks...")
        
        try:
            result = subprocess.run(
                ['wsl', '--unmount'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log("✅ All disks unmounted successfully")
                self.mounted_disks.clear()
                self.last_mount_path = None
                self.open_mount_btn.setEnabled(False)
                QMessageBox.information(self, "Success", "All disks unmounted successfully.")
            else:
                error_msg = result.stderr or result.stdout
                self.log(f"❌ Unmount failed: {error_msg}")
                QMessageBox.warning(self, "Unmount Failed", f"Failed to unmount:\n{error_msg}")
        
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred:\n{str(e)}")
    
    def get_mount_path(self, distro_name: str, disk: DiskInfo, partition_num: int) -> Optional[str]:
        """Get the actual mount path for the partition"""
        try:
            # Query WSL for mounted devices
            result = subprocess.run(
                ['wsl', '-d', distro_name, '--', 'bash', '-c', 'lsblk -o NAME,MOUNTPOINT -J'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Look for mounted block devices under /mnt/wsl
                for device in data.get('blockdevices', []):
                    if 'children' in device:
                        for child in device['children']:
                            mountpoint = child.get('mountpoint', '')
                            if mountpoint and '/mnt/wsl' in mountpoint:
                                # Found a mount under /mnt/wsl
                                # Convert to Windows path
                                windows_path = f"\\\\wsl$\\{distro_name}{mountpoint}"
                                return windows_path
                    
                    # Check parent device too
                    mountpoint = device.get('mountpoint', '')
                    if mountpoint and '/mnt/wsl' in mountpoint:
                        windows_path = f"\\\\wsl$\\{distro_name}{mountpoint}"
                        return windows_path
            
            # Fallback: construct default path
            return f"\\\\wsl$\\{distro_name}\\mnt\\wsl"
        
        except Exception as e:
            self.log(f"Could not determine exact mount path: {e}")
            return f"\\\\wsl$\\{distro_name}\\mnt\\wsl"
    
    def open_mount_location(self, path: str):
        """Open the mount location in Windows File Explorer"""
        try:
            # Use Windows explorer to open the path
            subprocess.Popen(['explorer', path], shell=True)
            self.log(f"📂 Opened {path} in File Explorer")
        except Exception as e:
            self.log(f"❌ Could not open File Explorer: {e}")
            
            # Try alternative method using QDesktopServices
            try:
                url = QUrl.fromLocalFile(path)
                QDesktopServices.openUrl(url)
            except Exception as e2:
                self.log(f"❌ Alternative method also failed: {e2}")
                QMessageBox.warning(
                    self,
                    "Could Not Open",
                    f"Could not open File Explorer automatically.\n\n"
                    f"Please manually navigate to:\n{path}"
                )
    
    def open_last_mount(self):
        """Open the last mounted location"""
        if self.last_mount_path:
            self.open_mount_location(self.last_mount_path)
        else:
            QMessageBox.information(
                self,
                "No Mount",
                "No partition has been mounted yet.\n\n"
                "Please mount a partition first."
            )
    
    def show_instructions(self):
        """Show usage instructions"""
        instructions = """
<h2>WSL Ext4 Partition Mounter - Instructions</h2>

<h3>Prerequisites:</h3>
<ul>
<li>Windows 11 or Windows 10 with WSL2 installed</li>
<li>At least one WSL distribution (e.g., Ubuntu)</li>
<li>Administrator privileges</li>
<li>External drive with ext4 partition OR dual-boot Linux partition</li>
</ul>

<h3>How to Use:</h3>
<ol>
<li><b>Scan Disks:</b> Click "Scan Disks" to detect available physical disks</li>
<li><b>Select Disk:</b> Click on a disk from the list</li>
<li><b>Choose Partition:</b> Select the partition number from the dropdown</li>
<li><b>Select Filesystem:</b> Choose the filesystem type (usually ext4)</li>
<li><b>Mount:</b> Click "Mount Partition"</li>
<li><b>Access:</b> Open File Explorer and navigate to \\\\wsl$\\&lt;distro&gt;\\mnt\\wsl\\</li>
</ol>

<h3>Important Limitations:</h3>
<ul>
<li>Cannot mount partitions on the same physical disk as Windows installation</li>
<li>Entire disk is attached to WSL2 (even if mounting just one partition)</li>
<li>USB flash drives and SD cards may not work reliably</li>
<li>Requires WSL2, not WSL1</li>
</ul>

<h3>Troubleshooting:</h3>
<ul>
<li>Run as Administrator</li>
<li>Ensure WSL2 is installed: <code>wsl --version</code></li>
<li>Update WSL: <code>wsl --update</code></li>
<li>Check if disk is in use by Windows</li>
</ul>

<h3>Unmounting:</h3>
<p>Click "Unmount All" when finished to safely detach all disks.</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Instructions")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(instructions)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = WSLMounter()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
