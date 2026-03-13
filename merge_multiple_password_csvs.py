import pandas as pd
from urllib.parse import urlparse
import os

# CONFIGURATION
# Add your file paths here
INPUT_FILES = [
    {'path': 'chrome_passwords.csv', 'source': 'Chrome'},
    {'path': 'brave_passwords.csv', 'source': 'Brave'},
    {'path': 'bitwarden_ios_export.csv', 'source': 'iOS_Keychain'}
]

OUTPUT_CLEAN = 'final_import_bitwarden.csv'
OUTPUT_CONFLICTS = 'conflicts_to_review.csv'

def normalize_url(url):
    """
    Strips protocol, www, and trailing slashes to compare domains/paths.
    """
    if not isinstance(url, str) or not url.strip():
        return ''
    
    # Add protocol if missing for parsing
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
        
    parsed = urlparse(url)
    netloc = parsed.netloc.replace('www.', '')
    path = parsed.path.rstrip('/')
    
    return f"{netloc}{path}"

def load_and_standardize(file_info):
    """
    Loads a CSV and maps it to a standard Bitwarden-compatible schema.
    """
    path = file_info['path']
    source = file_info['source']
    
    if not os.path.exists(path):
        print(f"Warning: File {path} not found. Skipping.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return pd.DataFrame()

    # Standardize Column Names
    # Chrome/Brave usually export: name, url, username, password
    # Bitwarden exports: login_uri, login_username, login_password, name, etc.
    
    rename_map = {}
    
    # Detect format based on columns
    cols = [c.lower() for c in df.columns]
    
    if 'login_uri' in cols: # Bitwarden format
        rename_map = {
            'login_uri': 'url',
            'login_username': 'username',
            'login_password': 'password',
            'name': 'name'
        }
    elif 'url' in cols and 'username' in cols: # Chrome/Brave format
        rename_map = {
            'url': 'url',
            'username': 'username',
            'password': 'password',
            'name': 'name'
        }
    
    # Rename and select only necessary columns
    df.rename(columns=lambda x: rename_map.get(x.lower(), x), inplace=True)
    
    required_cols = ['url', 'username', 'password', 'name']
    for col in required_cols:
        if col not in df.columns:
            df[col] = '' # Fill missing columns
            
    df = df[required_cols].copy()
    df['source'] = source
    
    # Clean data
    df.fillna('', inplace=True)
    df['normalized_url'] = df['url'].apply(normalize_url)
    
    return df

def process_passwords():
    all_data = []
    for f in INPUT_FILES:
        print(f"Processing {f['source']}...")
        all_data.append(load_and_standardize(f))
        
    if not all_data:
        print("No data loaded.")
        return

    full_df = pd.concat(all_data, ignore_index=True)
    
    print(f"Total entries loaded: {len(full_df)}")

    # 1. EXACT DUPLICATES
    # Same URL (normalized), Username, AND Password
    # We keep the first occurrence and drop the rest
    deduped_df = full_df.drop_duplicates(
        subset=['normalized_url', 'username', 'password'], 
        keep='first'
    )
    print(f"Entries after removing exact duplicates: {len(deduped_df)}")

    # 2. CONFLICT DETECTION
    # Same URL and Username, but DIFFERENT Password
    # We mark these for manual review
    
    # Group by URL and Username
    groups = deduped_df.groupby(['normalized_url', 'username'])
    
    clean_rows = []
    conflict_rows = []

    for (url, user), group in groups:
        if len(group) == 1:
            clean_rows.append(group)
        else:
            # Check if passwords actually differ (ignoring empty passwords)
            passwords = set(group['password'].replace('', pd.NA).dropna())
            
            if len(passwords) <= 1:
                # If multiple entries but same password (or empty), take the one with the most info
                # Sort by length of 'name' or 'url' to pick the "best" one
                best_entry = group.sort_values(by='url', key=lambda x: x.str.len(), ascending=False).iloc[[0]]
                clean_rows.append(best_entry)
            else:
                # Genuine conflict: Same user/site, different passwords
                conflict_rows.append(group)

    # Compile Clean Data
    if clean_rows:
        final_clean = pd.concat(clean_rows)
        
        # Format for Bitwarden Import
        # Bitwarden expects: login_uri, login_username, login_password, name
        bitwarden_export = pd.DataFrame({
            'login_uri': final_clean['url'],
            'login_username': final_clean['username'],
            'login_password': final_clean['password'],
            'name': final_clean['name']
        })
        
        bitwarden_export.to_csv(OUTPUT_CLEAN, index=False)
        print(f"SUCCESS: Cleaned data written to {OUTPUT_CLEAN} ({len(bitwarden_export)} entries)")

    # Compile Conflicts
    if conflict_rows:
        final_conflicts = pd.concat(conflict_rows)
        final_conflicts = final_conflicts.sort_values(by=['normalized_url', 'username'])
        final_conflicts.to_csv(OUTPUT_CONFLICTS, index=False)
        print(f"ATTENTION: {len(final_conflicts)} conflicting entries written to {OUTPUT_CONFLICTS}. Please review manually.")
    else:
        print("No conflicts found!")

if __name__ == "__main__":
    process_passwords()
