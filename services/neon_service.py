import os
import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import boto3
from dotenv import dotenv_values, load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment configs
load_dotenv(BASE_DIR / ".env")
neon_env = dotenv_values(BASE_DIR / "neon-storage.env")

# Neon Cloud Storage Config
S3_ENDPOINT = neon_env.get("AWS_ENDPOINT_URL_S3") or os.getenv("AWS_ENDPOINT_URL_S3")
S3_ACCESS_KEY = neon_env.get("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
S3_SECRET_KEY = neon_env.get("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
S3_REGION = neon_env.get("AWS_REGION") or os.getenv("AWS_REGION", "ap-southeast-1")
BUCKET_NAME = "uploads"

DATABASE_URL = os.getenv("DATABASE_URL") or neon_env.get("DATABASE_URL")


class NeonStorageManager:
    def __init__(self):
        self.client = None
        if S3_ENDPOINT and S3_ACCESS_KEY and S3_SECRET_KEY:
            try:
                self.client = boto3.client(
                    "s3",
                    endpoint_url=S3_ENDPOINT,
                    aws_access_key_id=S3_ACCESS_KEY,
                    aws_secret_access_key=S3_SECRET_KEY,
                    region_name=S3_REGION,
                )
            except Exception as e:
                print(f"[NeonStorage] Init warning: {e}")

    def upload_bytes(self, file_bytes: bytes, file_name: str, content_type: str = "image/jpeg") -> Optional[str]:
        if not self.client:
            return None
        try:
            key = f"media/{file_name}"
            self.client.put_object(
                Bucket=BUCKET_NAME,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
            )
            return f"{S3_ENDPOINT}/{BUCKET_NAME}/{key}"
        except Exception as e:
            print(f"[NeonStorage] Upload failed: {e}")
            return None

    def upload_file(self, file_path: str, key_name: Optional[str] = None) -> Optional[str]:
        if not self.client or not os.path.exists(file_path):
            return None
        key = key_name or Path(file_path).name
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            return self.upload_bytes(data, key)
        except Exception as e:
            print(f"[NeonStorage] Upload file error: {e}")
            return None

    def read_json(self, key: str) -> Optional[Any]:
        if not self.client:
            return None
        try:
            resp = self.client.get_object(Bucket=BUCKET_NAME, Key=key)
            return json.loads(resp["Body"].read().decode("utf-8"))
        except Exception:
            return None

    def write_json(self, key: str, data: Any) -> bool:
        if not self.client:
            return False
        try:
            self.client.put_object(
                Bucket=BUCKET_NAME,
                Key=key,
                Body=json.dumps(data, indent=2).encode("utf-8"),
                ContentType="application/json",
            )
            return True
        except Exception as e:
            print(f"[NeonStorage] write_json error for {key}: {e}")
            return False


class NeonDBManager:
    """Cloud-synced Neon Database manager using Neon S3/Postgres backend."""
    def __init__(self, storage: NeonStorageManager):
        self.storage = storage
        self.is_postgres = False
        self.db_path = BASE_DIR / "data" / "autoinsta.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._sync_from_neon_cloud()

    def _get_connection(self):
        if DATABASE_URL and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")):
            try:
                import psycopg2
                conn = psycopg2.connect(DATABASE_URL)
                self.is_postgres = True
                return conn
            except Exception as e:
                print(f"[NeonDB] Postgres direct connect failed, using cloud-synced store: {e}")
        return sqlite3.connect(str(self.db_path))

    def _init_db(self):
        conn = self._get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                avatar_url TEXT,
                followers INTEGER DEFAULT 0,
                category TEXT,
                is_connected BOOLEAN DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS generated_assets (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                image_url TEXT,
                video_url TEXT,
                audio_url TEXT,
                thumbnail_url TEXT,
                caption TEXT,
                hashtags TEXT,
                aspect_ratio TEXT,
                content_type TEXT,
                prompt TEXT,
                created_at TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id TEXT PRIMARY KEY,
                account_id TEXT,
                asset_id TEXT,
                scheduled_time TEXT,
                status TEXT,
                recurrence TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS brand_kits (
                account_id TEXT PRIMARY KEY,
                brand_name TEXT,
                primary_color TEXT,
                secondary_color TEXT,
                font_tone TEXT,
                signature_hashtags TEXT,
                cta_text TEXT
            )
        """)

        # Seed default accounts
        cur.execute("SELECT COUNT(*) FROM accounts")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("""
                INSERT INTO accounts (id, username, display_name, avatar_url, followers, category, is_connected)
                VALUES 
                ('acc_1', 'artisan_bakery_nyc', 'Artisan Bakery NYC', 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=150', 24800, 'Food & Beverage', 1),
                ('acc_2', 'apex_fitness_club', 'Apex Fitness Club', 'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=150', 61200, 'Health & Fitness', 1),
                ('acc_3', 'lumina_skincare', 'Lumina Organic Skincare', 'https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=150', 43500, 'Beauty & Wellness', 0)
            """)

        conn.commit()
        conn.close()

    def _sync_from_neon_cloud(self):
        """Pulls persistent state from Neon Cloud Storage."""
        try:
            cloud_accounts = self.storage.read_json("db/accounts.json")
            if cloud_accounts:
                conn = self._get_connection()
                cur = conn.cursor()
                for a in cloud_accounts:
                    cur.execute("""
                        INSERT OR REPLACE INTO accounts (id, username, display_name, avatar_url, followers, category, is_connected)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (a["id"], a["username"], a["displayName"], a["avatarUrl"], a["followers"], a["category"], 1 if a.get("isConnected") else 0))
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"[NeonDB] Cloud pull warning: {e}")

    def _push_to_neon_cloud(self, table_name: str):
        """Pushes local state snapshot to Neon Cloud Storage for 100% remote persistence."""
        try:
            if table_name == "accounts":
                data = self.get_accounts()
                self.storage.write_json("db/accounts.json", data)
            elif table_name == "scheduled_posts":
                data = self.get_scheduled_posts()
                self.storage.write_json("db/scheduled_posts.json", data)
        except Exception as e:
            print(f"[NeonDB] Cloud push warning for {table_name}: {e}")

    def get_accounts(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, username, display_name, avatar_url, followers, category, is_connected FROM accounts")
        rows = cur.fetchall()
        accounts = []
        for r in rows:
            accounts.append({
                "id": r[0],
                "username": r[1],
                "displayName": r[2],
                "avatarUrl": r[3],
                "followers": r[4],
                "category": r[5],
                "isConnected": bool(r[6]),
            })
        conn.close()
        return accounts

    def toggle_account_connect(self, account_id: str) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT is_connected FROM accounts WHERE id = ?", (account_id,))
        row = cur.fetchone()
        if row:
            new_val = 0 if row[0] else 1
            cur.execute("UPDATE accounts SET is_connected = ? WHERE id = ?", (new_val, account_id))
            conn.commit()
            conn.close()
            self._push_to_neon_cloud("accounts")
            return bool(new_val)
        conn.close()
        return False

    def save_generated_asset(self, asset: Dict[str, Any]) -> str:
        conn = self._get_connection()
        cur = conn.cursor()
        asset_id = asset.get("id") or ("ast_" + str(int(time.time() * 1000)))
        cur.execute("""
            INSERT OR REPLACE INTO generated_assets 
            (id, account_id, image_url, video_url, audio_url, thumbnail_url, caption, hashtags, aspect_ratio, content_type, prompt, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset_id,
            asset.get("accountId", "acc_1"),
            asset.get("imageUrl"),
            asset.get("videoUrl"),
            asset.get("audioUrl"),
            asset.get("thumbnailUrl"),
            asset.get("caption"),
            json.dumps(asset.get("hashtags", [])),
            asset.get("aspectRatio", "9:16"),
            asset.get("contentType", "reel"),
            asset.get("prompt"),
            asset.get("createdAt"),
        ))
        conn.commit()
        conn.close()
        # Save individual asset to Neon Cloud
        self.storage.write_json(f"db/assets/{asset_id}.json", asset)
        return asset_id

    def get_scheduled_posts(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT s.id, s.account_id, s.scheduled_time, s.status, s.recurrence,
                   a.image_url, a.video_url, a.audio_url, a.thumbnail_url, a.caption, a.hashtags, a.aspect_ratio, a.content_type, a.prompt, a.created_at
            FROM scheduled_posts s
            LEFT JOIN generated_assets a ON s.asset_id = a.id
            ORDER BY s.scheduled_time ASC
        """)
        rows = cur.fetchall()
        posts = []
        for r in rows:
            hashtags = []
            if r[10]:
                try:
                    hashtags = json.loads(r[10])
                except Exception:
                    hashtags = []
            posts.append({
                "id": r[0],
                "accountId": r[1],
                "scheduledTime": r[2],
                "status": r[3],
                "recurrence": r[4],
                "asset": {
                    "imageUrl": r[5] or "",
                    "videoUrl": r[6] or "",
                    "audioUrl": r[7] or "",
                    "thumbnailUrl": r[8] or "",
                    "caption": r[9] or "",
                    "hashtags": hashtags,
                    "aspectRatio": r[11] or "9:16",
                    "contentType": r[12] or "reel",
                    "prompt": r[13] or "",
                    "createdAt": r[14] or "",
                }
            })
        conn.close()
        return posts

    def add_scheduled_post(self, post_data: Dict[str, Any]) -> str:
        conn = self._get_connection()
        cur = conn.cursor()
        post_id = post_data.get("id") or ("sch_" + str(int(time.time() * 1000)))
        asset_id = self.save_generated_asset(post_data.get("asset", {}))
        cur.execute("""
            INSERT OR REPLACE INTO scheduled_posts (id, account_id, asset_id, scheduled_time, status, recurrence)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            post_id,
            post_data.get("accountId", "acc_1"),
            asset_id,
            post_data.get("scheduledTime"),
            post_data.get("status", "scheduled"),
            post_data.get("recurrence", "none"),
        ))
        conn.commit()
        conn.close()
        self._push_to_neon_cloud("scheduled_posts")
        return post_id

    def delete_scheduled_post(self, post_id: str) -> bool:
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM scheduled_posts WHERE id = ?", (post_id,))
        conn.commit()
        conn.close()
        self._push_to_neon_cloud("scheduled_posts")
        return True

    def get_brand_kit(self, account_id: str) -> Dict[str, Any]:
        # Try cloud first
        cloud_kit = self.storage.read_json(f"db/brandkits/{account_id}.json")
        if cloud_kit:
            return cloud_kit

        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("SELECT brand_name, primary_color, secondary_color, font_tone, signature_hashtags, cta_text FROM brand_kits WHERE account_id = ?", (account_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            tags = []
            if row[4]:
                try:
                    tags = json.loads(row[4])
                except Exception:
                    tags = []
            return {
                "brandName": row[0],
                "primaryColor": row[1],
                "secondaryColor": row[2],
                "fontTone": row[3],
                "signatureHashtags": tags,
                "ctaText": row[5],
            }
        return {
            "brandName": "Artisan Brand",
            "primaryColor": "#E07A5F",
            "secondaryColor": "#F4F1DE",
            "fontTone": "Warm & Artisanal",
            "signatureHashtags": ["#Brand", "#Trending"],
            "ctaText": "Link in bio to purchase!",
        }

    def save_brand_kit(self, account_id: str, kit: Dict[str, Any]):
        conn = self._get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO brand_kits (account_id, brand_name, primary_color, secondary_color, font_tone, signature_hashtags, cta_text)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            account_id,
            kit.get("brandName"),
            kit.get("primaryColor"),
            kit.get("secondaryColor"),
            kit.get("fontTone"),
            json.dumps(kit.get("signatureHashtags", [])),
            kit.get("ctaText"),
        ))
        conn.commit()
        conn.close()
        # Save to Neon Cloud directly
        self.storage.write_json(f"db/brandkits/{account_id}.json", kit)


neon_storage = NeonStorageManager()
neon_db = NeonDBManager(neon_storage)
