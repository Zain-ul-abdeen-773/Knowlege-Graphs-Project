"""
PKG2020 Knowledge Graph - Fuseki Data Loader
Script to upload TTL data to Apache Jena Fuseki SPARQL server
"""
import os
import sys
import requests
import time
from pathlib import Path

# Configuration
FUSEKI_URL = os.environ.get('FUSEKI_URL', 'http://localhost:3030')
DATASET_NAME = os.environ.get('FUSEKI_DATASET', 'pkg2020')
ADMIN_USER = os.environ.get('FUSEKI_USER', 'admin')
ADMIN_PASS = os.environ.get('FUSEKI_PASS', 'admin123')

# Paths
SCRIPT_DIR = Path(__file__).parent
OWL_DIR = SCRIPT_DIR.parent / 'owl'
TTL_FILE = OWL_DIR / 'pkg2020_final.ttl'
OWL_FILE = OWL_DIR / 'pkg2020_final.owl'


def wait_for_fuseki(max_retries=30, delay=2):
    """Wait for Fuseki server to be ready"""
    print(f"⏳ Waiting for Fuseki at {FUSEKI_URL}...")
    
    for i in range(max_retries):
        try:
            resp = requests.get(f"{FUSEKI_URL}/$/ping", timeout=5)
            if resp.status_code == 200:
                print("✅ Fuseki is ready!")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(delay)
        print(f"   Retry {i+1}/{max_retries}...")
    
    print("❌ Fuseki did not become ready")
    return False


def create_dataset():
    """Create the dataset if it doesn't exist"""
    print(f"\n📦 Creating dataset '{DATASET_NAME}'...")
    
    # Check if dataset exists
    resp = requests.get(
        f"{FUSEKI_URL}/$/datasets/{DATASET_NAME}",
        auth=(ADMIN_USER, ADMIN_PASS)
    )
    
    if resp.status_code == 200:
        print(f"   Dataset '{DATASET_NAME}' already exists")
        return True
    
    # Create dataset
    resp = requests.post(
        f"{FUSEKI_URL}/$/datasets",
        auth=(ADMIN_USER, ADMIN_PASS),
        data={
            'dbType': 'tdb2',
            'dbName': DATASET_NAME
        }
    )
    
    if resp.status_code in [200, 201]:
        print(f"✅ Dataset '{DATASET_NAME}' created!")
        return True
    else:
        print(f"❌ Failed to create dataset: {resp.status_code} - {resp.text}")
        return False


def get_data_file():
    """Get the best available data file"""
    if TTL_FILE.exists():
        return TTL_FILE, 'text/turtle'
    elif OWL_FILE.exists():
        return OWL_FILE, 'application/rdf+xml'
    else:
        return None, None


def upload_data():
    """Upload RDF data to Fuseki"""
    data_file, content_type = get_data_file()
    
    if not data_file:
        print("❌ No data file found!")
        print(f"   Looking for: {TTL_FILE}")
        print(f"   Or: {OWL_FILE}")
        return False
    
    file_size_mb = data_file.stat().st_size / (1024 * 1024)
    print(f"\n📤 Uploading {data_file.name} ({file_size_mb:.1f} MB)...")
    print("   This may take several minutes for large files...")
    
    # Upload endpoint
    upload_url = f"{FUSEKI_URL}/{DATASET_NAME}/data"
    
    try:
        with open(data_file, 'rb') as f:
            resp = requests.post(
                upload_url,
                auth=(ADMIN_USER, ADMIN_PASS),
                headers={'Content-Type': content_type},
                data=f,
                timeout=3600  # 1 hour timeout for large files
            )
        
        if resp.status_code in [200, 201, 204]:
            print("✅ Data uploaded successfully!")
            return True
        else:
            print(f"❌ Upload failed: {resp.status_code}")
            print(f"   Response: {resp.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Upload timed out (file may be too large)")
        return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False


def verify_upload():
    """Verify data was uploaded by running a test query"""
    print("\n🔍 Verifying upload...")
    
    query = "SELECT (COUNT(*) AS ?count) WHERE { ?s ?p ?o }"
    
    resp = requests.get(
        f"{FUSEKI_URL}/{DATASET_NAME}/sparql",
        params={'query': query},
        headers={'Accept': 'application/json'}
    )
    
    if resp.status_code == 200:
        data = resp.json()
        count = data.get('results', {}).get('bindings', [{}])[0].get('count', {}).get('value', 0)
        print(f"✅ Graph contains {int(count):,} triples")
        return True
    else:
        print(f"❌ Verification failed: {resp.status_code}")
        return False


def main():
    print("=" * 60)
    print("  PKG2020 Knowledge Graph - Fuseki Data Loader")
    print("=" * 60)
    print(f"\n  Fuseki URL: {FUSEKI_URL}")
    print(f"  Dataset: {DATASET_NAME}")
    print()
    
    # Wait for Fuseki
    if not wait_for_fuseki():
        sys.exit(1)
    
    # Create dataset
    if not create_dataset():
        sys.exit(1)
    
    # Upload data
    if not upload_data():
        sys.exit(1)
    
    # Verify
    verify_upload()
    
    print("\n" + "=" * 60)
    print("  ✅ Setup Complete!")
    print("=" * 60)
    print(f"\n  SPARQL Endpoint: {FUSEKI_URL}/{DATASET_NAME}/sparql")
    print(f"  Fuseki UI: {FUSEKI_URL}")
    print()


if __name__ == '__main__':
    main()
