import aiosqlite
from typing import Optional, List, Dict, Any
from config import DB_PATH

async def init_db() -> None:
    """Ma'lumotlar bazasi va jadvallarini ishga tushirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                activity_description TEXT NOT NULL,
                address_hours TEXT NOT NULL,
                delivery_payment TEXT NOT NULL,
                latitude REAL,
                longitude REAL,
                business_connection_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Migratsiya: latitude va longitude ustunlarini qo'shish (agar avvaldan mavjud bo'lmasa)
        try:
            await db.execute("ALTER TABLE businesses ADD COLUMN latitude REAL;")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE businesses ADD COLUMN longitude REAL;")
        except Exception:
            pass
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES businesses (user_id) ON DELETE CASCADE
            );
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_connection_id TEXT NOT NULL,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                message_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Indekslar
        await db.execute("CREATE INDEX IF NOT EXISTS idx_business_user_id ON businesses(user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_business_conn_id ON businesses(business_connection_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_faqs_user_id ON faqs(user_id);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_chat_hist ON chat_history(business_connection_id, chat_id);")
        
        await db.commit()

async def get_business_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Tadbirkor ma'lumotlarini user_id orqali olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM businesses WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
    return None

async def get_business_by_connection_id(connection_id: str) -> Optional[Dict[str, Any]]:
    """Tadbirkor ma'lumotlarini Telegram Business connection_id orqali olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM businesses WHERE business_connection_id = ?", (connection_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
    return None

async def create_or_update_business(
    user_id: int,
    company_name: str,
    activity_description: str,
    address_hours: str,
    delivery_payment: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> None:
    """Tadbirkor ma'lumotlarini yaratish yoki yangilash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO businesses (user_id, company_name, activity_description, address_hours, delivery_payment, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                company_name = excluded.company_name,
                activity_description = excluded.activity_description,
                address_hours = excluded.address_hours,
                delivery_payment = excluded.delivery_payment,
                latitude = excluded.latitude,
                longitude = excluded.longitude;
        """, (user_id, company_name, activity_description, address_hours, delivery_payment, latitude, longitude))
        await db.commit()

async def update_business_connection(user_id: int, connection_id: Optional[str]) -> None:
    """Telegram Business connection_id ni yangilash yoki o'chirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE businesses SET business_connection_id = ? WHERE user_id = ?",
            (connection_id, user_id)
        )
        await db.commit()

async def set_business_status(user_id: int, is_active: bool) -> None:
    """Botning faollik statusini yoqish yoki to'xtatish"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE businesses SET is_active = ? WHERE user_id = ?",
            (1 if is_active else 0, user_id)
        )
        await db.commit()

async def add_faq(user_id: int, question: str, answer: str) -> int:
    """Yangi savol-javob qo'shish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO faqs (user_id, question, answer) VALUES (?, ?, ?)",
            (user_id, question.strip(), answer.strip())
        )
        await db.commit()
        return cursor.lastrowid

async def get_faqs(user_id: int) -> List[Dict[str, Any]]:
    """Tadbirkorning barcha savol-javoblarini olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM faqs WHERE user_id = ? ORDER BY id ASC", (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_faq_by_id(faq_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Bitta FAQ ni ID orqali olish"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM faqs WHERE id = ? AND user_id = ?", (faq_id, user_id)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
    return None

async def delete_faq(faq_id: int, user_id: int) -> bool:
    """FAQ ni o'chirish"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "DELETE FROM faqs WHERE id = ? AND user_id = ?", (faq_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def add_chat_history(business_connection_id: str, chat_id: int, role: str, message_text: str) -> None:
    """Mijoz va AI o'rtasidagi suhbat xabarini saqlash"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chat_history (business_connection_id, chat_id, role, message_text) VALUES (?, ?, ?, ?)",
            (business_connection_id, chat_id, role, message_text)
        )
        await db.commit()

async def get_recent_chat_history(business_connection_id: str, chat_id: int, limit: int = 5) -> List[Dict[str, str]]:
    """Oxirgi suhbat tarixini xronologik tartibda olish (limit = 5)"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT role, message_text 
            FROM chat_history 
            WHERE business_connection_id = ? AND chat_id = ? 
            ORDER BY id DESC 
            LIMIT ?
            """,
            (business_connection_id, chat_id, limit)
        ) as cursor:
            rows = await cursor.fetchall()
            # Eng eskidan yangiga tartiblash
            history = [{"role": row["role"], "message_text": row["message_text"]} for row in reversed(rows)]
            return history
