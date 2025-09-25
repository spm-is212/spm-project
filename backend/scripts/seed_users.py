import os
from backend.utils.security import hash_password
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

# Example users you want to insert
users = [
    {
        "email": "shi@example.com",
        "password": "password123",
        "role": "user",
        "departments": ["IT"], 
    },
    {
        "email": "manager@example.com",
        "password": "admin123",
        "role": "manager",
        "departments": ["IT"], 

    },
]

def seed_users():
    crud = SupabaseCRUD()

    for user in users:
        hashed_pw = hash_password(user["password"])  # bcrypt-hash it
        data = {
            "email": user["email"],
            "password_hash": hashed_pw,
            "role": user["role"],
            "departments": user["departments"]
        }
        # Insert into Supabase
        res = crud.client.table("users").insert(data).execute()
        print(f"Inserted user: {user['email']} -> {res}")

if __name__ == "__main__":
    seed_users()
