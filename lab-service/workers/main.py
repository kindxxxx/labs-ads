"""ARQ worker — запуск: python -m workers.main"""

from __future__ import annotations

from arq import cron
from arq.connections import RedisSettings

from config.settings import get_settings
from workers import tasks

settings = get_settings()


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    functions = [
        tasks.notify_user,
        tasks.notify_admin_receipt,
        tasks.cleanup_temp_files,
    ]
    cron_jobs = [
        cron(tasks.cleanup_temp_files, hour={0, 6, 12, 18}, minute=0),
    ]


if __name__ == "__main__":
    from arq import run_worker

    run_worker(WorkerSettings)
