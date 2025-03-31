from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import LinkCreate, UserCreate, LinkUpdate
from models import User, ExpiredLink
from auth import create_access_token, get_current_user
import random
import string
from sqlalchemy.future import select
from models import Link
from database import redis_client
from datetime import datetime, timedelta
from fastapi import BackgroundTasks
from httpx import URL


router = APIRouter()


def generate_short_code(short_code_length = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=short_code_length))


@router.post("/links/shorten")
async def shorten_link(link_data: LinkCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    short_code = link_data.custom_alias or generate_short_code()

    result = await db.execute(select(Link).where(Link.short_code == short_code))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Alias already exists")

    expires_at = link_data.expires_at
    if expires_at and expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="Expired link expired")

    new_link = Link(
        short_code=short_code,
        original_url=str(link_data.original_url),
        expires_at=expires_at,
        user_id=user.id if user else None
    )

    db.add(new_link)
    await db.commit()
    await redis_client.set(short_code, str(link_data.original_url), ex=expires_at - datetime.now() if expires_at else None)

    return {"short_code": short_code, "original_url": link_data.original_url, "expires_at": expires_at}


@router.get("/links/{short_code}")
async def redirect(short_code: str, db: AsyncSession = Depends(get_db)):
    original_url = await redis_client.get(short_code)

    if not original_url:
        result = await db.execute(select(Link).where(Link.short_code == short_code))
        link = result.scalars().first()
        if not link or (link.expires_at and link.expires_at < datetime.utcnow()):
            raise HTTPException(status_code=404, detail="Short link not found or expired")

        await redis_client.set(short_code, str(link.original_url))
        link.click_count += 1
        link.last_used_at = datetime.utcnow()
        await db.commit()

        original_url = URL(link.original_url)

    return {"redirect_url": original_url}


@router.delete("/links/{short_code}")
async def delete_link(short_code: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    await db.delete(link)
    await db.commit()

    await redis_client.delete(short_code)

    return {"message": "Link deleted successfully"}


@router.put("/links/{short_code}")
async def update_link(link_data: LinkUpdate, db: AsyncSession = Depends(get_db),
                      user=Depends(get_current_user)):
    result = await db.execute(select(Link).where(Link.short_code == link_data.short_code))
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    if link.user_id != user.id:
        raise HTTPException(status_code=403, detail="Permission denied")

    link.original_url = URL(link_data.original_url)
    link.last_updated_at = datetime.utcnow()

    await db.commit()

    await redis_client.set(link_data.short_code, link_data.original_url)

    return {"message": "Link updated successfully", "short_code": link_data.short_code, "new_url": link_data.original_url}


@router.get("/links/{short_code}/stats")
async def link_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return {
        "original_url": link.original_url,
        "created_at": link.created_at,
        "click_count": link.visit_count,
        "last_used_at": link.last_used_at,
        "expires_at": link.expires_at
    }


@router.get("/links/search")
async def search_link(original_url: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Link).where(Link.original_url == original_url))
    links = result.scalars().all()

    if not links:
        raise HTTPException(status_code=404, detail="No links found for this URL")

    return [{"short_code": link.short_code, "created_at": link.created_at} for link in links]


@router.post("/auth/register")
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = User.hash_password(user_data.password)
    new_user = User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    await db.commit()
    return {"message": "User registered successfully"}


@router.post("/auth/token")
async def login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalars().first()

    if not user or not user.verify_password(user_data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(user.id)

    return {"access_token": access_token, "token_type": "bearer"}


async def delete_unused_links(db: AsyncSession, cleanup_days: int):
    expiration_date = datetime.utcnow() - timedelta(days=cleanup_days)
    result = await db.execute(select(Link).where(Link.last_used_at < expiration_date))
    links_to_delete = result.scalars().all()

    for link in links_to_delete:
        expired_link = ExpiredLink(
            short_code=link.short_code,
            original_url=link.original_url,
            created_at=link.created_at,
            last_used_at=link.last_used_at,
            visit_count=link.visit_count,
            user_id=link.user_id
        )
        db.add(expired_link)
        await db.delete(link)

    await db.commit()


@router.post("/set_cleanup_days")
async def cleanup_unused_links(background_tasks: BackgroundTasks, cleanup_days: int, db: AsyncSession = Depends(get_db)):
    background_tasks.add_task(delete_unused_links, db, cleanup_days)
    return {"message": "Cleanup started in background"}

@router.get("/links/expired")
async def get_expired_links(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ExpiredLink))
    return result.scalars().all()


