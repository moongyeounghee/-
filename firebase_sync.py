import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# 싱글톤 패턴으로 초기화 (여러 번 호출되어도 한 번만 초기화)
def init_firebase():
    if not firebase_admin._apps:
        # 1. 클라우드 환경 (Streamlit Secrets) 시도
        try:
            import streamlit as st
            if "firebase" in st.secrets:
                cert_dict = dict(st.secrets["firebase"])
                cred = credentials.Certificate(cert_dict)
                firebase_admin.initialize_app(cred)
                return True
        except Exception:
            pass
            
        # 2. 로컬 테스트 환경 (D드라이브) 시도
        try:
            cred = credentials.Certificate(r"d:\donwnload\credentials.json")
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            print(f"🔥 Firebase 초기화 실패: {e}")
            return False
    return True

def get_db():
    if init_firebase():
        return firestore.client()
    return None

def send_ping(flight_no, msg):
    """오프라인 핑(Ping)을 파이어베이스 클라우드로 쏩니다"""
    db = get_db()
    if not db: return False
    
    try:
        doc_ref = db.collection("pings").document(flight_no.upper())
        doc_ref.set({
            "msg": msg,
            "time": datetime.now().strftime("%H:%M:%S"),
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        print(f"🔥 Ping 전송 실패: {e}")
        return False

def get_ping(flight_no):
    """클라우드에서 최신 핑(Ping)을 당겨옵니다"""
    db = get_db()
    if not db: return None
    
    try:
        doc_ref = db.collection("pings").document(flight_no.upper())
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        print(f"🔥 Ping 수신 실패: {e}")
    return None
