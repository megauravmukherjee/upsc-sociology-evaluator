import os
import sys

def test_imports():
    print("Testing core module imports...")
    import config
    from core.evaluator import load_vault
    
    vault = load_vault()
    print(f"Vault loaded successfully with {len(vault.get('definitions', []))} definitions.")
    print("All core modules imported cleanly!")

if __name__ == "__main__":
    test_imports()
