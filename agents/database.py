import firebase_admin
import json
from firebase_admin import credentials, firestore

def init_firestore(config_path="config.json"):
    """Initialize Firestore client from config.json."""
    with open(config_path) as f:
        config = json.load(f)
    cred = credentials.Certificate(config)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    return firestore.client()

def upload_to_firestore(data, collection="resumes", config_path="config.json"):
    """Upload data to Firestore, using candidate name as document ID."""
    db = init_firestore(config_path)
    candidate_name = data.get("candidate_name", "unknown_candidate")
    doc_id = candidate_name.replace(" ", "_")
    doc_ref = db.collection(collection).document(doc_id)
    doc_ref.set(data)
    return doc_id