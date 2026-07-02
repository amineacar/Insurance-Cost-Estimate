import pyodbc
import hashlib
import streamlit as st

# ── VERİTABANI AYARLARI ────────────────────────────────────────────────
SERVER_NAME = "localhost"
DB_NAME = "InsuranceDB"

def get_ms_sql_connection():
    """MS SQL Server'a Windows Authentication ile bağlanır."""
    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def init_ms_sql():
    """Master veritabanına bağlanıp önce InsuranceDB'yi, sonra tabloları otomatik oluşturur."""
    try:
        master_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE=master;Trusted_Connection=yes;"
        conn = pyodbc.connect(master_str, autocommit=True)
        cursor = conn.cursor()
        cursor.execute(f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{DB_NAME}') CREATE DATABASE {DB_NAME}")
        conn.close()

        conn = get_ms_sql_connection()
        cursor = conn.cursor()

        # 1. Predictions Tablosu (Mevcut Tablonuz)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[predictions]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[predictions] (
                    [id] INT IDENTITY(1,1) PRIMARY KEY,
                    [age] INT,
                    [height] INT,
                    [weight] INT,
                    [bmi] FLOAT,
                    [gender] VARCHAR(10),
                    [children] INT,
                    [smoker] VARCHAR(5),
                    [region] VARCHAR(20),
                    [estimated_cost] FLOAT,
                    [username] VARCHAR(50),
                    [timestamp] DATETIME DEFAULT GETDATE()
                )
            END
        """)

        # 2. Users Tablosu (Kimlik Doğrulama Tablosu)
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND type in (N'U'))
            BEGIN
                CREATE TABLE [dbo].[users] (
                    [id] INT IDENTITY(1,1) PRIMARY KEY,
                    [username] VARCHAR(50) UNIQUE NOT NULL,
                    [password_hash] VARCHAR(64) NOT NULL,
                    [role] VARCHAR(20) DEFAULT 'user',
                    [created_at] DATETIME DEFAULT GETDATE()
                )
                
                -- Varsayılan Admin Hesabı Oluşturma (Şifre: admin123)
                INSERT INTO [dbo].[users] (username, password_hash, role)
                VALUES ('admin', '2400af518e1675500914028d2fda9d5e6499e8a3330b2343ee61c403ddcc9ed9', 'admin')
            END
        """)

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"MS SQL Connection Error: {e}. Please check the SERVER_NAME field.")

def hash_password(password):
    """Güvenlik standardı olarak şifreyi SHA-256 ile hashler."""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    """Yeni kullanıcı kaydeder."""
    try:
        conn = get_ms_sql_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'user')",
            (username, hash_password(password))
        )
        conn.commit()
        conn.close()
        return True, "Registration successful! You can now sign in."
    except pyodbc.IntegrityError:
        return False, "This username is already taken!"
    except Exception as e:
        return False, f"Error: {e}"

def login_user(username, password):
    """Kullanıcı giriş kontrolü yapar ve rolünü döner."""
    # 🎯 ADMIN KONTROLÜ: Veritabanına sormadan doğrudan admin'i kabul et
    if username == "admin@gmail.com" and password == "admin123":
        return True, "admin"
        
    try:
        conn = get_ms_sql_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username = ? AND password_hash = ?",
            (username, hash_password(password))
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return True, row[0]
        return False, None
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False, None
    
def log_prediction(age, height, weight, bmi, sex, children, smoker, region, estimated_cost, username):
    """Inserts a new prediction log into the MS SQL database."""
    try:
        conn = get_ms_sql_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (age, height, weight, bmi, gender, children, smoker, region, estimated_cost, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (age, height, weight, round(bmi, 2), sex, children, smoker, region, round(estimated_cost, 2), username))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database write error: {e}")
        return False