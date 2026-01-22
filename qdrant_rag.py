"""Qdrant RAG integration with VoyageAI embeddings"""
import os
import json
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import voyageai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class QdrantRAG:
    """RAG system using Qdrant Cloud and VoyageAI embeddings"""
    
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY", "")
        self.voyage_model = os.getenv("VOYAGE_MODEL_NAME", "voyage-3-large")
        self.collection_name = os.getenv("QDRANT_COLLECTION_NAME", "repair_manuals")
        
        # Initialize clients
        try:
            self.client = QdrantClient(
                url=self.qdrant_url,
                api_key=self.qdrant_api_key if self.qdrant_api_key else None,
                prefer_grpc=False
            )
            print(f"[OK] Connected to Qdrant: {self.qdrant_url}")
        except Exception as e:
            print(f"[WARN] Qdrant connection error: {e}")
            self.client = None
        
        if self.voyage_api_key and self.voyage_api_key not in ["pa-placeholder-add-your-key", ""]:
            try:
                self.voyage_client = voyageai.Client(api_key=self.voyage_api_key)
                print(f"[OK] Connected to VoyageAI with model: {self.voyage_model}")
            except Exception as e:
                print(f"[WARN] VoyageAI initialization error: {e}")
                self.voyage_client = None
        else:
            self.voyage_client = None
            print("[WARN] VoyageAI API key not configured - embeddings disabled")
        
        if self.client:
            try:
                self._ensure_collection_exists()
                if self.voyage_client:
                    self._seed_sample_data()
            except Exception as e:
                print(f"⚠ Collection initialization error: {e}")
    
    def _ensure_collection_exists(self):
        """Create collection if doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except:
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1024,  # VoyageAI voyage-3-large dimension
                    distance=Distance.COSINE
                )
            )
            print(f"[OK] Created collection: {self.collection_name}")
    
    def _seed_sample_data(self):
        """Seed sample repair manuals if collection is empty"""
        try:
            count = self.client.count(self.collection_name).count
            if count == 0:
                self._populate_sample_manuals()
        except:
            print("Could not seed data - collection may be pre-populated")
    
    def _populate_sample_manuals(self):
        """Populate with sample repair data"""
        sample_manuals = [
            {
                "id": 1,
                "device_model": "SMS6EDI06E",
                "device_name": "Bosch Dishwasher Serie 6 SMS6EDI06E",
                "symptoms": "no water entry, error code E:15",
                "steps": [
                    "Step 1: Check water inlet valve - listen for buzzing sound",
                    "Step 2: Inspect inlet hose for kinks or blockages",
                    "Step 3: Test water pressure at inlet - should be 0.3-1 MPa",
                    "Step 4: Replace inlet valve if water doesn't flow",
                    "Step 5: Reset error code and run test cycle"
                ],
                "resolution": "Replace water inlet valve - common failure"
            },
            {
                "id": 2,
                "device_model": "SMS6EDI06E",
                "device_name": "Bosch Dishwasher Serie 6 SMS6EDI06E",
                "symptoms": "error code E:25, excessive noise during pump",
                "steps": [
                    "Step 1: Inspect drain filter for foreign objects",
                    "Step 2: Check pump impeller rotation",
                    "Step 3: Verify pump seal condition",
                    "Step 4: Replace drain pump if damaged",
                    "Step 5: Run diagnostic cycle to verify"
                ],
                "resolution": "Replace drain pump assembly"
            },
            {
                "id": 3,
                "device_model": "WAX28E91",
                "device_name": "Bosch Washing Machine WAX28E91",
                "symptoms": "not spinning, clothes still wet",
                "steps": [
                    "Step 1: Check door lock mechanism",
                    "Step 2: Inspect belt for wear or breaks",
                    "Step 3: Test motor operation with continuity tester",
                    "Step 4: Replace belt if worn",
                    "Step 5: Verify spin cycle functionality"
                ],
                "resolution": "Replace drive belt - normal wear item"
            },
            {
                "id": 4,
                "device_model": "RF32CG5100",
                "device_name": "Samsung French Door Refrigerator RF32CG5100",
                "symptoms": "not cooling, ice buildup in freezer",
                "steps": [
                    "Step 1: Defrost evaporator coils",
                    "Step 2: Check refrigerant lines for blockage",
                    "Step 3: Test compressor start relay",
                    "Step 4: Verify thermostat sensor function",
                    "Step 5: Replace air damper if stuck"
                ],
                "resolution": "Defrost cycle + component testing required"
            },
            {
                "id": 5,
                "device_model": "LCRM1650",
                "device_name": "LG Microwave Oven LCRM1650",
                "symptoms": "no heating, fan works",
                "steps": [
                    "Step 1: Test magnetron continuity",
                    "Step 2: Check high-voltage transformer",
                    "Step 3: Inspect power supply board",
                    "Step 4: Replace magnetron if failed",
                    "Step 5: Run heating test cycle"
                ],
                "resolution": "Replace magnetron tube - common failure"
            }
        ]
        
        # Embed and store
        for manual in sample_manuals:
            text = f"{manual['device_name']} {manual['symptoms']} {' '.join(manual['steps'])}"
            
            # Get embedding from VoyageAI
            embedding = self.get_embedding(text)
            
            if embedding:
                point = PointStruct(
                    id=manual["id"],
                    vector=embedding,
                    payload={
                        "device_model": manual["device_model"],
                        "device_name": manual["device_name"],
                        "symptoms": manual["symptoms"],
                        "steps": manual["steps"],
                        "resolution": manual["resolution"]
                    }
                )
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
        print(f"Seeded {len(sample_manuals)} repair manuals")
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get VoyageAI embedding for text"""
        if not self.voyage_client:
            return None
        
        try:
            result = self.voyage_client.embed(
                text,
                model=self.voyage_model
            )
            return result.embeddings[0]
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def search_solutions(
        self,
        device_model: str,
        symptoms_summary: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search for repair solutions using device model + symptom embeddings
        Returns top-k similar repair manuals
        """
        if not self.client or not self.voyage_client:
            return []
        
        # Build query text
        query_text = f"Device: {device_model} Symptoms: {symptoms_summary}"
        
        # Get embedding
        query_embedding = self.get_embedding(query_text)
        if not query_embedding:
            return []
        
        # Search Qdrant
        try:
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=0.3
            )
            
            solutions = []
            for result in results:
                solutions.append({
                    "score": result.score,
                    "device_model": result.payload.get("device_model"),
                    "device_name": result.payload.get("device_name"),
                    "symptoms": result.payload.get("symptoms"),
                    "steps": result.payload.get("steps"),
                    "resolution": result.payload.get("resolution")
                })
            
            return solutions
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def add_manual(self, manual: Dict) -> bool:
        """Add new repair manual to database"""
        try:
            text = f"{manual['device_name']} {manual['symptoms']}"
            embedding = self.get_embedding(text)
            
            if not embedding:
                return False
            
            # Get next ID
            count = self.client.count(self.collection_name).count
            next_id = count + 1
            
            point = PointStruct(
                id=next_id,
                vector=embedding,
                payload=manual
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return True
        except Exception as e:
            print(f"Error adding manual: {e}")
            return False
