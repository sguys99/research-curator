"""Scheduler package for automated data collection and email sending."""

from app.scheduler.main import scheduler, start_scheduler, stop_scheduler

__all__ = ["scheduler", "start_scheduler", "stop_scheduler"]
