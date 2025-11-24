#from app.controllers.auth_controller import get_password_hash

from app.repositories.user_repository import UserRepository
from app.models.DTO.user_dto import UserDTO
from app.models.user_type import UserType
from app.database.database import reset_db, init_db as init_database

import asyncio

async def init_db():
    await init_database()

    repo = UserRepository()

    # Check if admin already exists
    try: 
        res = await repo.get_user_by_username("admin")
        if res is not None:
            print("ℹ️ Admin user already exists")
    except:
        admin_dto = UserDTO(username="admin", password="admin", type=UserType.Administrator)
        manager_dto = UserDTO(username="ShopManager", password="ShManager", type=UserType.ShopManager)
        cashier_dto = UserDTO(username="Cashier", password="Cashier", type=UserType.Cashier)
        await repo.create_user(admin_dto.username, admin_dto.password, admin_dto.type)
        await repo.create_user(manager_dto.username, manager_dto.password, manager_dto.type)
        await repo.create_user(cashier_dto.username, cashier_dto.password, cashier_dto.type)
        print("✅ Admin user created successfully")

async def reset():
    await reset_db()
    print("✅ Database reset successfully")
    
if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(init_db())
    #loop.run_until_complete(reset())
