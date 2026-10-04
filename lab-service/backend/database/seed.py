"""Заполнение каталога лабораторных из config/labs.py.

Запуск: python -m backend.database.seed
"""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import SessionLocal, engine
from backend.models import Base, Lab, LabLanguage, Language
from config.labs import LABS


async def seed_labs(session: AsyncSession) -> None:
    lang_cache: dict[str, Language] = {}

    for subject, labs in LABS.items():
        for lab_number, seed in labs.items():
            result = await session.execute(
                select(Lab).where(
                    Lab.subject == subject, Lab.lab_number == lab_number
                )
            )
            lab = result.scalar_one_or_none()
            if lab is None:
                lab = Lab(
                    subject=subject,
                    lab_number=lab_number,
                    price=seed.price,
                    description=seed.description,
                    requirements=seed.requirements,
                    is_active=True,
                )
                session.add(lab)
                await session.flush()
            else:
                lab.price = seed.price
                lab.description = seed.description
                lab.requirements = seed.requirements
                lab.is_active = True

            # refresh languages for lab
            await session.execute(
                LabLanguage.__table__.delete().where(LabLanguage.lab_id == lab.id)
            )
            for lang_name in seed.languages:
                if lang_name not in lang_cache:
                    res = await session.execute(
                        select(Language).where(Language.name == lang_name)
                    )
                    lang = res.scalar_one_or_none()
                    if lang is None:
                        lang = Language(name=lang_name)
                        session.add(lang)
                        await session.flush()
                    lang_cache[lang_name] = lang
                session.add(LabLanguage(lab_id=lab.id, language_id=lang_cache[lang_name].id))

    await session.commit()


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        await seed_labs(session)
    print("Seed completed.")


if __name__ == "__main__":
    asyncio.run(main())
