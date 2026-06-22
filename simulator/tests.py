import json
import subprocess
import sys
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from simulator.backend.models import AsyncGenerator, Breaker, ConsumerLoad, Load, Meter, Source, Transformer
from simulator.backend.services.model_loader import ModelLoader
from simulator.backend.services.simulator import Simulator


class TestElectricalSimulatorCore(unittest.TestCase):
    def setUp(self):
        self.model = ModelLoader.load_example_model()
        self.simulator = Simulator(self.model)
        self.simulator.simulate_step()

    def state(self, component_id):
        return self.simulator.get_system_state().components[component_id]

    def test_model_loading_uses_current_example_model(self):
        self.assertEqual(len(self.model.components), 12)
        self.assertEqual(sum(isinstance(c, Source) for c in self.model.components), 1)
        self.assertEqual(sum(isinstance(c, Transformer) for c in self.model.components), 1)
        self.assertEqual(sum(isinstance(c, Breaker) for c in self.model.components), 2)
        self.assertEqual(sum(isinstance(c, Load) for c in self.model.components), 1)
        self.assertEqual(sum(isinstance(c, ConsumerLoad) for c in self.model.components), 1)
        self.assertEqual(sum(isinstance(c, AsyncGenerator) for c in self.model.components), 1)
        self.assertEqual(sum(isinstance(c, Meter) for c in self.model.components), 2)

    def test_transformer_step_down_and_step_up_math(self):
        transformer = next(c for c in self.model.components if isinstance(c, Transformer))

        self.assertAlmostEqual(self.simulator._calculate_transformer_voltage(transformer, 13800), 480, places=0)
        self.assertAlmostEqual(self.simulator._calculate_transformer_voltage(transformer, 480), 13800, places=0)

    def test_opening_main_breaker_de_energizes_everything_downstream(self):
        self.assertTrue(self.simulator.update_breaker_state("breaker-main", False))
        self.simulator.simulate_step()

        self.assertTrue(self.state("source-1")["energized"])
        self.assertTrue(self.state("bus-main")["energized"])
        self.assertTrue(self.state("meter-main")["energized"])
        self.assertFalse(self.state("bus-load")["energized"])
        self.assertFalse(self.state("breaker-load")["energized"])
        self.assertFalse(self.state("load-panel")["energized"])
        self.assertFalse(self.state("load-1")["energized"])
        self.assertFalse(self.state("consumer-load-1")["energized"])
        self.assertFalse(self.state("meter-load")["energized"])

    def test_opening_load_breaker_de_energizes_only_load_side(self):
        self.assertTrue(self.simulator.update_breaker_state("breaker-load", False))
        self.simulator.simulate_step()

        self.assertTrue(self.state("breaker-main")["energized"])
        self.assertTrue(self.state("bus-load")["energized"])
        self.assertFalse(self.state("load-panel")["energized"])
        self.assertFalse(self.state("load-1")["energized"])
        self.assertFalse(self.state("consumer-load-1")["energized"])
        self.assertFalse(self.state("meter-load")["energized"])
        self.assertTrue(self.state("meter-main")["energized"])

    def test_closing_breakers_restores_voltage_when_upstream_is_energized(self):
        self.simulator.update_breaker_state("breaker-main", False)
        self.simulator.update_breaker_state("breaker-load", False)
        self.simulator.simulate_step()
        self.assertFalse(self.state("load-1")["energized"])

        self.simulator.update_breaker_state("breaker-main", True)
        self.simulator.update_breaker_state("breaker-load", True)
        self.simulator.simulate_step()

        self.assertTrue(self.state("load-1")["energized"])
        self.assertAlmostEqual(self.state("load-1")["voltage"], 480, places=0)

    def test_meter_readings_include_basic_power_values(self):
        load_meter = self.state("meter-load")

        self.assertTrue(load_meter["energized"])
        self.assertAlmostEqual(load_meter["voltage"], 480, places=0)
        self.assertGreater(load_meter["current"], 0)
        self.assertAlmostEqual(load_meter["real_power"], 300, places=1)
        self.assertGreater(load_meter["reactive_power"], 0)
        self.assertGreater(load_meter["apparent_power"], load_meter["real_power"])
        self.assertGreater(load_meter["power_factor"], 0)
        self.assertLessEqual(load_meter["power_factor"], 1)
        self.assertAlmostEqual(load_meter["frequency"], 60, places=1)

    def test_invalid_ids_return_false_in_service(self):
        self.assertFalse(self.simulator.update_breaker_state("missing-breaker", False))
        self.assertFalse(self.simulator.update_consumer_load_draw("missing-load", True))
        self.assertFalse(self.simulator.update_async_generator_state("missing-generator", True))


class TestElectricalSimulatorApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 8031
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "simulator.backend.api:app",
                "--host",
                "127.0.0.1",
                "--port",
                str(cls.port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                cls.request("GET", "/health")
                return
            except Exception:
                time.sleep(0.2)
        cls.tearDownClass()
        raise RuntimeError("API server did not start")

    @classmethod
    def tearDownClass(cls):
        server = getattr(cls, "server", None)
        if server and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()

    @classmethod
    def request(cls, method, path):
        request = Request(f"{cls.base_url}{path}", method=method)
        try:
            with urlopen(request, timeout=5) as response:
                body = response.read().decode("utf-8")
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    return response.status, json.loads(body)
                return response.status, body
        except HTTPError as error:
            return error.code, error.read().decode("utf-8")

    def test_dashboard_and_state_endpoints_load(self):
        status, page = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("Electrical Diagram Simulator", page)

        model_status, model = self.request("GET", "/api/model")
        state_status, state = self.request("GET", "/api/state")
        self.assertEqual(model_status, 200)
        self.assertEqual(state_status, 200)
        self.assertEqual(len(model["components"]), 12)
        self.assertIn("components", state)

    def test_listed_api_endpoints_work(self):
        endpoints = [
            ("GET", "/api"),
            ("GET", "/health"),
            ("POST", "/api/simulate/step"),
            ("POST", "/api/model/reload"),
            ("GET", "/api/simulation/status"),
            ("POST", "/api/breakers/breaker-main/open"),
            ("POST", "/api/breakers/breaker-main/close"),
            ("POST", "/api/consumer_load/consumer-load-1/unexpected_draw?unexpected_draw_active=true"),
            ("POST", "/api/async_generator/async-generator-1/operational?operational=true"),
        ]
        for method, path in endpoints:
            status, _ = self.request(method, path)
            self.assertEqual(status, 200, path)

    def test_invalid_ids_return_404(self):
        endpoints = [
            ("POST", "/api/breakers/not-real/open"),
            ("POST", "/api/consumer_load/not-real/unexpected_draw?unexpected_draw_active=true"),
            ("POST", "/api/async_generator/not-real/operational?operational=true"),
        ]
        for method, path in endpoints:
            status, _ = self.request(method, path)
            self.assertEqual(status, 404, path)


if __name__ == "__main__":
    unittest.main()
