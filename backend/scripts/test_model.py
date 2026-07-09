from app.database.postgres import SessionLocal
from app.models import User


db = SessionLocal()

user = User(
    username="khang",
    email="khang@test.com",
    hashed_password="hashed_password"
)

db.add(user)
db.commit()
db.refresh(user)

print(user.id)
print(user.username)

db.close()