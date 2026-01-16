"""
Ollama Path Fixer Tool
----------------------
Diagnoses and fixes broken Ollama installations on Windows.
1. Finds missing Ollama executable
2. Adds it to Windows User PATH
3. Sets OLLAMA_MODELS environment variable
"""

import os
import sys
import winreg
import shutil
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_ollama():
    print("🔍 Searching for Ollama executable...")
    
    # Check PATH first
    path = shutil.which("ollama")
    if path:
        print(f"✅ Found in PATH: {path}")
        return path, os.path.dirname(path)

    # Check default locations
    local_app_data = os.environ.get("LOCALAPPDATA")
    candidates = [
        os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe"),
        os.path.join(local_app_data, "Ollama", "ollama.exe"),
        r"C:\Program Files\Ollama\ollama.exe"
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            print(f"⚠️ Found in directory (missing from PATH): {candidate}")
            return candidate, os.path.dirname(candidate)
            
    print("❌ Could not find Ollama. Is it installed?")
    return None, None

def update_user_env_var(name, value):
    """Update a user environment variable in the registry."""
    key_path = r"Environment"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        try:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
            print(f"✅ Set {name} = {value}")
            return True
        except Exception as e:
            print(f"❌ Failed to set {name}: {e}")
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        print(f"❌ Could not open registry key: {e}")
    return False

def add_to_path(directory):
    """Add directory to User PATH."""
    key_path = r"Environment"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        try:
            path_value, _ = winreg.QueryValueEx(key, "Path")
            
            if directory.lower() in path_value.lower():
                print("✅ Directory already in PATH")
                return True
                
            new_path = path_value + ";" + directory
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            print(f"✅ Added to PATH: {directory}")
            print("ℹ️  You may need to restart your terminal/IDE for changes to take effect.")
            return True
            
        except FileNotFoundError:
            # Path variable doesn't exist? Create it
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, directory)
            return True
        finally:
            winreg.CloseKey(key)
    except Exception as e:
        print(f"❌ Registry error: {e}")
        return False

def main():
    print("=== Ollama System Fixer ===\n")
    
    exe_path, directory = find_ollama()
    
    if not directory:
        print("\n❌ Cannot fix PATH because Ollama executable was not found.")
        input("\nPress Enter to exit...")
        return

    print(f"\n1. Fixing PATH variable...")
    add_to_path(directory)

    print(f"\n2. Configuring OLLAMA_MODELS...")
    current_models = os.environ.get("OLLAMA_MODELS", "Not Set")
    print(f"   Current value: {current_models}")
    
    # Default to T:\OllamaModels if it exists, otherwise ask
    default_models = r"T:\OllamaModels"
    if not os.path.exists(default_models):
        default_models = ""
    
    choice = input(f"   Set OLLAMA_MODELS to '{default_models}'? (Y/n/custom): ").strip().lower()
    
    target_dir = default_models
    if choice == 'n':
        target_dir = None
    elif choice != 'y' and choice != '':
        target_dir = choice

    if target_dir:
        if not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir)
                print(f"   Created directory: {target_dir}")
            except:
                print(f"   ⚠️ Warning: Directory {target_dir} does not exist")
        
        update_user_env_var("OLLAMA_MODELS", target_dir)
        print("\n✅ Configuration complete!")
        print("   IMPORTANT: You must restart the Ollama app/service for this to take effect.")
        print("   Run: taskkill /f /im ollama.exe")
    
    print("\nDone. Please restart your terminals and the LLM Bridge.")
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()
