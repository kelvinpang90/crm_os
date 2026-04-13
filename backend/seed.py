"""
Seed script: creates test data for development.
Run: python seed.py
"""
import asyncio
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal

from passlib.context import CryptContext
from sqlalchemy import text

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.contact import Contact
from app.models.activity import Activity
from app.models.task import Task

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


async def seed():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        if count and count > 0:
            print("Database already seeded. Skipping.")
            return

        # --- Users ---
        admin_id = str(uuid.uuid4())
        manager_id = str(uuid.uuid4())
        sales_id = str(uuid.uuid4())

        users = [
            User(
                id=admin_id,
                name="系统管理员",
                email="admin@crm.com",
                password_hash=hash_password("Admin123"),
                role="admin",
                language="zh",
            ),
            User(
                id=manager_id,
                name="销售主管张伟",
                email="manager@crm.com",
                password_hash=hash_password("Manager123"),
                role="manager",
                language="zh",
            ),
            User(
                id=sales_id,
                name="销售代表李娜",
                email="sales@crm.com",
                password_hash=hash_password("Sales123"),
                role="sales",
                language="zh",
                manager_id=manager_id,
            ),
        ]
        session.add_all(users)

        # --- Contacts (10, covering all industries & statuses) ---
        industries = [
            "科技/IT", "金融/保险", "医疗/健康", "教育/培训", "零售/电商",
            "制造/工业", "房地产", "咨询/服务", "餐饮/酒店", "物流/供应链",
        ]
        statuses = ["潜在客户", "跟进中", "谈判中", "已成交", "已流失"]
        priorities = ["高", "中", "低"]

        contacts = []
        contact_ids = []
        today = date.today()

        contact_data = [
            ("王建国", "北京科技有限公司", 0, 0, 0, Decimal("500000.00"), "wang@tech.com", "13800001111"),
            ("陈丽华", "上海金融集团", 1, 1, 1, Decimal("1200000.00"), "chen@finance.com", "13800002222"),
            ("刘明辉", "广州健康医疗", 2, 2, 0, Decimal("800000.00"), "liu@health.com", "13800003333"),
            ("赵晓雯", "深圳教育科技", 3, 3, 2, Decimal("350000.00"), "zhao@edu.com", "13800004444"),
            ("孙浩然", "杭州电商平台", 4, 4, 1, Decimal("2000000.00"), "sun@ecom.com", "13800005555"),
            ("周美玲", "东莞制造集团", 5, 0, 0, Decimal("1500000.00"), "zhou@mfg.com", "13800006666"),
            ("吴志强", "成都房地产开发", 6, 1, 2, Decimal("5000000.00"), "wu@estate.com", "13800007777"),
            ("郑思远", "南京咨询公司", 7, 2, 1, Decimal("600000.00"), "zheng@consult.com", "13800008888"),
            ("马晓峰", "武汉餐饮连锁", 8, 3, 0, Decimal("450000.00"), "ma@food.com", "13800009999"),
            ("黄雅琴", "重庆物流科技", 9, 0, 2, Decimal("750000.00"), "huang@logistics.com", "13800000000"),
        ]

        for i, (name, company, ind_i, stat_i, pri_i, deal, email, phone) in enumerate(contact_data):
            cid = str(uuid.uuid4())
            contact_ids.append(cid)
            contacts.append(
                Contact(
                    id=cid,
                    name=name,
                    company=company,
                    industry=industries[ind_i],
                    status=statuses[stat_i],
                    priority=priorities[pri_i],
                    deal_value=deal,
                    email=email,
                    phone=phone,
                    assigned_to=sales_id if i % 2 == 0 else manager_id,
                    last_contact=today - timedelta(days=i * 3),
                    tags=["重要客户"] if pri_i == 0 else ["普通客户"],
                    notes=f"{name}的客户备注信息",
                )
            )
        session.add_all(contacts)

        # --- Activities (at least 1 per contact) ---
        activity_types = ["电话", "邮件", "会面", "WhatsApp", "其他"]
        activities = []
        for i, cid in enumerate(contact_ids):
            activities.append(
                Activity(
                    id=str(uuid.uuid4()),
                    contact_id=cid,
                    user_id=sales_id if i % 2 == 0 else manager_id,
                    type=activity_types[i % len(activity_types)],
                    content=f"与{contact_data[i][0]}进行了{activity_types[i % len(activity_types)]}沟通，讨论合作事宜。",
                    follow_date=datetime.utcnow() - timedelta(days=i * 2),
                )
            )
        # Extra activities for some contacts
        for i in range(3):
            activities.append(
                Activity(
                    id=str(uuid.uuid4()),
                    contact_id=contact_ids[i],
                    user_id=sales_id,
                    type="会面",
                    content=f"第二次拜访{contact_data[i][0]}，深入了解需求。",
                    follow_date=datetime.utcnow() - timedelta(days=1),
                )
            )
        session.add_all(activities)

        # --- Tasks (5) ---
        tasks = [
            Task(
                id=str(uuid.uuid4()),
                title="联系王建国确认报价单",
                contact_id=contact_ids[0],
                assigned_to=sales_id,
                priority="高",
                due_date=today,
                is_done=False,
            ),
            Task(
                id=str(uuid.uuid4()),
                title="准备陈丽华项目方案书",
                contact_id=contact_ids[1],
                assigned_to=manager_id,
                priority="高",
                due_date=today + timedelta(days=2),
                is_done=False,
            ),
            Task(
                id=str(uuid.uuid4()),
                title="回访刘明辉了解产品使用情况",
                contact_id=contact_ids[2],
                assigned_to=sales_id,
                priority="中",
                due_date=today + timedelta(days=5),
                is_done=False,
            ),
            Task(
                id=str(uuid.uuid4()),
                title="整理本月销售数据报表",
                contact_id=None,
                assigned_to=manager_id,
                priority="中",
                due_date=today - timedelta(days=1),
                is_done=True,
                done_at=datetime.utcnow() - timedelta(hours=5),
            ),
            Task(
                id=str(uuid.uuid4()),
                title="发送合同给赵晓雯",
                contact_id=contact_ids[3],
                assigned_to=sales_id,
                priority="低",
                due_date=today + timedelta(days=7),
                is_done=True,
                done_at=datetime.utcnow() - timedelta(days=2),
            ),
        ]
        session.add_all(tasks)

        await session.commit()
        print("Seed data created successfully!")
        print(f"  Admin:   admin@crm.com / Admin123")
        print(f"  Manager: manager@crm.com / Manager123")
        print(f"  Sales:   sales@crm.com / Sales123")


if __name__ == "__main__":
    asyncio.run(seed())
