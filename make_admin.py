from database import get_connection
email = input("Email admin: ")
conn = get_connection()
conn.execute("UPDATE users SET role = 'admin' WHERE email = ?", (email,))
conn.commit()
conn.close()
print("✅ Done!")