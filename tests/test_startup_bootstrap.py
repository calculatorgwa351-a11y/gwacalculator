import asyncio
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch


from app import main


class StartupBootstrapTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        main.bootstrap_task = None
        main._set_bootstrap_state(status="pending", started_at=None, finished_at=None, error=None)

    async def test_health_endpoint_reports_bootstrap_metadata(self):
        main._set_bootstrap_state(
            status="running",
            started_at="2026-04-04T09:38:44+00:00",
            finished_at=None,
            error=None,
        )

        payload = await main.health_check()

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["bootstrap_status"], "running")
        self.assertEqual(payload["bootstrap_started_at"], "2026-04-04T09:38:44+00:00")
        self.assertIsNone(payload["bootstrap_finished_at"])
        self.assertIsNone(payload["bootstrap_error"])

    async def test_background_startup_returns_before_bootstrap_finishes(self):
        gate = threading.Event()
        original_to_thread = asyncio.to_thread

        def blocking_sequence():
            gate.wait(timeout=2)

        async def delayed_to_thread(func, *args, **kwargs):
            if func is main._run_bootstrap_sequence:
                return await original_to_thread(blocking_sequence)
            return await original_to_thread(func, *args, **kwargs)

        test_settings = SimpleNamespace(
            app_env="production",
            database_backend="postgresql",
            init_db_on_startup=True,
            startup_bootstrap_mode="background",
            is_production=True,
        )

        with patch.object(main, "settings", test_settings), patch.object(
            main, "_database_target", return_value="db.example/postgres"
        ), patch.object(main, "_dist_ready", return_value=True), patch.object(
            main.asyncio, "to_thread", side_effect=delayed_to_thread
        ):
            await main.startup_event()
            self.assertIsNotNone(main.bootstrap_task)

            await asyncio.sleep(0)
            payload = await main.health_check()
            self.assertEqual(payload["bootstrap_status"], "pending")

            gate.set()
            await asyncio.wait_for(main.bootstrap_task, timeout=2)

    async def test_background_bootstrap_transitions_to_ready(self):
        async def immediate_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        test_settings = SimpleNamespace(
            app_env="production",
            database_backend="postgresql",
            init_db_on_startup=True,
            startup_bootstrap_mode="background",
            is_production=True,
        )

        with patch.object(main, "settings", test_settings), patch.object(
            main, "_database_target", return_value="db.example/postgres"
        ), patch.object(main, "_dist_ready", return_value=True), patch.object(
            main, "_run_bootstrap_sequence"
        ) as run_bootstrap, patch.object(main.asyncio, "to_thread", side_effect=immediate_to_thread):
            run_bootstrap.side_effect = lambda: main._set_bootstrap_state(
                status="ready",
                started_at="start",
                finished_at="finish",
                error=None,
            )

            await main.startup_event()
            await asyncio.wait_for(main.bootstrap_task, timeout=2)

            payload = await main.health_check()
            self.assertEqual(payload["bootstrap_status"], "ready")
            self.assertEqual(payload["bootstrap_finished_at"], "finish")

    def test_bootstrap_failure_sets_failed_state(self):
        test_settings = SimpleNamespace(database_backend="sqlite")

        with patch.object(main, "settings", test_settings), patch.object(
            main, "_try_acquire_bootstrap_lock", return_value=True
        ), patch.object(main, "run_lightweight_migrations"), patch.object(
            main, "init_database", side_effect=RuntimeError("boom")
        ):
            with self.assertRaises(RuntimeError):
                main._run_bootstrap_sequence()

        self.assertEqual(main.bootstrap_state.status, "failed")
        self.assertEqual(main.bootstrap_state.error, "boom")
        self.assertIsNotNone(main.bootstrap_state.finished_at)

    def test_follower_worker_skips_duplicate_bootstrap(self):
        test_settings = SimpleNamespace(database_backend="postgresql")

        with patch.object(main, "settings", test_settings), patch.object(
            main, "_try_acquire_bootstrap_lock", return_value=False
        ), patch.object(main, "run_lightweight_migrations") as run_migrations, patch.object(
            main, "init_database"
        ) as init_database:
            main._run_bootstrap_sequence()

        run_migrations.assert_not_called()
        init_database.assert_not_called()
        self.assertEqual(main.bootstrap_state.status, "ready")
        self.assertIsNone(main.bootstrap_state.error)


if __name__ == "__main__":
    unittest.main()
