import sys
import subprocess
import platform

def install_dependencies():
    """Install the required dependencies."""
    print("Installing core dependencies...")
    
    # Core dependencies
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "flask==2.0.1", 
                          "flask-cors>=3.0.10",
                          "together>=1.4.6", 
                          "requests>=2.25.1"])
    
    # Install PyQt5 based on platform
    if platform.system() == "Windows":
        try:
            print("Installing PyQt5 for Windows...")
            # Try the binary package first
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyqt5-tools>=5.15.4"])
        except subprocess.CalledProcessError:
            print("Could not install pyqt5-tools, trying alternative...")
            try:
                # Try the binary wheel directly
                subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                      "--only-binary=pyqt5", "pyqt5==5.15.4"])
            except subprocess.CalledProcessError:
                print("Warning: Could not install PyQt5. GUI features will not be available.")
                print("You can try to install it manually with: pip install pyqt5==5.15.4")
    else:
        # For non-Windows platforms
        try:
            print("Installing PyQt5 for non-Windows platform...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "PyQt5==5.15.4"])
        except subprocess.CalledProcessError:
            print("Warning: Could not install PyQt5. GUI features will not be available.")
    
    print("Dependencies installation completed.")

if __name__ == "__main__":
    install_dependencies() 