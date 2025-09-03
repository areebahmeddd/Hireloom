import json
import firebase_admin
from firebase_admin import credentials, firestore


def db_init(config_path="firebase-config.json"):
    with open(config_path) as f:
        firebase_config = json.load(f)
    firebase_cred = credentials.Certificate(firebase_config)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(firebase_cred)
    return firestore.client()


def data_upload(data, collection="candidates", config_path="firebase-config.json"):
    firestore_db = db_init(config_path)
    candidate_name = data.get("candidate_name", "unknown_candidate")
    doc_id = candidate_name.replace(" ", "_")
    doc_ref = firestore_db.collection(collection).document(doc_id)
    doc_ref.set(data)
    return doc_id
