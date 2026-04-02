import time
import os
import json
import requests
import numpy as np
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor


class Benchmark:
    def __init__(self, url: str):
        self.url = url
        self.latencies = []
        self.resource_stats = {"cpu": [], "memory": []}
        self._stop_resources = False

    def _monitor_resources(self, interval=0.1):
        while not self._stop_resources:
            self.resource_stats["cpu"].append(psutil.cpu_percent(interval=None))
            self.resource_stats["memory"].append(psutil.virtual_memory().percent)
            time.sleep(interval)

    def _send_request(self, payload: dict):
        start = time.perf_counter()
        try:
            r = requests.post(self.url, params=payload, timeout=30)
            r.raise_for_status()

            return (time.perf_counter() - start) * 1000
        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса: {e}")
            return None

    def run(self, num_requests: int, concurrency: int, payload: dict, files_name: str = "benchmark_report"):
        self.latencies = []
        self.resource_stats = {"cpu": [], "memory": []}
        self._stop_resources = False
        os.makedirs("benchmark_data", exist_ok=True)

        monitor_thread = threading.Thread(target=self._monitor_resources)
        monitor_thread.start()

        print(f"Тест {self.url} ({num_requests} req, {concurrency} threads)...")
        start_test = time.perf_counter()

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(self._send_request, payload) for _ in range(num_requests)]
            for f in futures:
                res = f.result()
                if res:
                    self.latencies.append(res)

        total_time = time.perf_counter() - start_test

        self._stop_resources = True
        monitor_thread.join()

        self._report(total_time, concurrency, files_name)

    def _report(self, total_time, concurrency, files_name):
        if not self.latencies:
            print("Ошибка: Нет успешных ответов.")
            return

        rps = len(self.latencies) / total_time
        p50 = np.percentile(self.latencies, 50)
        p95 = np.percentile(self.latencies, 95)
        avg_cpu = np.mean(self.resource_stats["cpu"])
        max_mem = np.max(self.resource_stats["memory"])

        print(f"\n{'=' * 30}")
        print("PERFORMANCE:")
        print(f"  RPS:         {rps:.2f}")
        print(f"  P50 Latency: {p50:.2f} ms")
        print(f"  P95 Latency: {p95:.2f} ms")
        print("RESOURCES:")
        print(f"  Avg CPU:     {avg_cpu:.1f}%")
        print(f"  Max Memory:  {max_mem:.1f}%")
        print(f"{'=' * 30}\n")

        report_data = {
            "url": self.url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "concurrency": concurrency,
            "stats": {"rps": len(self.latencies) / total_time, "p50_ms": p50, "p95_ms": p95},
            "resources": {
                "avg_cpu_percent": avg_cpu,
                "max_mem_percent": max_mem,
            },
            "raw_latencies": self.latencies,
        }

        with open(f"benchmark_data/{files_name}", "x", encoding="utf-8") as f:
            json.dump(report_data, f, indent=4, ensure_ascii=False)
        print(f"Метрики сохранены в файл: benchmark_data/{files_name}")


if __name__ == "__main__":
    bench = Benchmark("http://0.0.0.0:8000/embed")
    light_payload = {"input": "Короткий текст"}
    heavy_payload = {"input": " ".join(["текст для теста"] * 100)}
    num_requests = 400

    concurrency_levels = [1, 4, 8, 16, 32, 64, 128]

    for i, concurrency in enumerate(concurrency_levels):
        print(f"\n--- ЗАПУСК ТЕСТА: Payload - Light, Concurrency = {concurrency} ---")

        bench.run(num_requests=num_requests, concurrency=concurrency, payload=light_payload, files_name=f"light_benchmark_report_{i + 1}")

        time.sleep(2)

    for i, concurrency in enumerate(concurrency_levels):
        print(f"\n--- ЗАПУСК ТЕСТА: Payload - Heavy, Concurrency = {concurrency} ---")

        bench.run(num_requests=num_requests, concurrency=concurrency, payload=heavy_payload, files_name=f"heavy_benchmark_report_{i + 1}")

        time.sleep(2)
