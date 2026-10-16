"""Bounded, replayable local search for nearly sharp thermal-lemma inputs."""

from __future__ import annotations

import os

# Set before NumPy/SciPy load, including in Windows-spawned workers.
for _thread_variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                         "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_thread_variable] = "1"

import argparse
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np
import scipy
from scipy.optimize import minimize

from validate_thermal import SOURCE_SHA256, UPSTREAM_COMMIT, audit_case, serialize_matrix

ROOT = Path(__file__).resolve().parents[1]
SHAPES = ((2, 2), (2, 3), (3, 2))
MIN_COEFFICIENT = 0.02
MIN_DETERMINANT = 0.005
MIN_U = 0.005
MIN_COMMUTATOR = 0.03
FEASIBILITY_TOLERANCE = 1e-8


class SearchBudget(Exception):
    pass


def decode(vector: np.ndarray, shape: tuple[int, int]):
    size = shape[0] * shape[1]
    x = (vector[:size] + 1j * vector[size:2 * size]).reshape(shape)
    y = (vector[2 * size:3 * size] + 1j * vector[3 * size:4 * size]).reshape(shape)
    nx, ny = np.linalg.norm(x), np.linalg.norm(y)
    if min(nx, ny) < 1e-15:
        raise ValueError("zero matrix parameter")
    x, y = x / nx, y / ny
    a, b, eta = vector[-3:]
    coefficient = np.array([a, b, eta, 1.0 - a - b - eta])
    return x, y, coefficient


def constraint_values(x: np.ndarray, y: np.ndarray, coefficient: np.ndarray) -> np.ndarray:
    a, b, eta, d = coefficient
    determinant = a * d - b * eta
    u = (a + b) * (eta + d) - determinant
    xx, yy = x @ x.conj().T, y @ y.conj().T
    commutator = float(np.linalg.norm(xx @ yy - yy @ xx))
    return np.r_[coefficient - MIN_COEFFICIENT,
                 determinant - MIN_DETERMINANT,
                 u - MIN_U, commutator - MIN_COMMUTATOR]


def full_record(vector: np.ndarray, shape: tuple[int, int]) -> dict:
    x, y, coefficient = decode(vector, shape)
    values = constraint_values(x, y, coefficient)
    assessment = audit_case(x, y, tuple(float(v) for v in coefficient))
    return {
        "X": serialize_matrix(x), "Y": serialize_matrix(y),
        "coefficient": coefficient.tolist(), "shape": list(shape),
        "residual_nats": assessment["residual_nats"],
        "minimum_constraint_margin": float(values.min()),
        "constraint_margins": values.tolist(),
        "gram_commutator_norm": float(values[-1] + MIN_COMMUTATOR),
        "phase_aligned_distance": float(np.sqrt(max(0.0, 2 - 2 * abs(np.vdot(x, y))))),
        "feasible": bool(values.min() >= -FEASIBILITY_TOLERANCE),
        "state_checks": {key: assessment[key] for key in (
            "maximum_trace_error", "maximum_hermitian_error", "minimum_eigenvalue")},
    }


def initial_point(rng: np.random.Generator, shape: tuple[int, int], deadline: float) -> np.ndarray:
    size = shape[0] * shape[1]
    for _ in range(10000):
        if time.monotonic() >= deadline:
            raise SearchBudget("deadline before feasible initialization")
        matrices = rng.normal(size=4 * size)
        coefficient = rng.dirichlet([3, 1, 1, 3])
        vector = np.r_[matrices, coefficient[:3]]
        x, y, coefficient = decode(vector, shape)
        if constraint_values(x, y, coefficient).min() > 0:
            return vector
    raise RuntimeError(f"could not initialize feasible point for {shape}")


def one_start(task: dict) -> dict:
    task_start = time.monotonic()
    rng = np.random.default_rng(task["seed"])
    shape = tuple(task["shape"])
    vector = initial_point(rng, shape, task["deadline"])
    initial = full_record(vector, shape)
    best = initial
    best_value = initial["residual_nats"]
    journal_path = Path(task["journal"])
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    evaluations, improvements = 0, 0
    best_vector = vector.copy()
    suspected_failures = 0

    with journal_path.open("x", encoding="utf-8") as journal:
        def write_record(event: str, record: dict) -> None:
            journal.write(json.dumps({"event": event, "start_id": task["id"],
                                      "seed": task["seed"], "evaluations": evaluations,
                                      "elapsed_seconds": time.monotonic() - task_start,
                                      **record}, allow_nan=False) + "\n")
            journal.flush()

        write_record("initial_feasible_point", initial)

        def constraints(raw: np.ndarray) -> np.ndarray:
            if time.monotonic() >= task["deadline"]:
                raise SearchBudget("global wall deadline")
            try:
                x, y, coefficient = decode(raw, shape)
                return constraint_values(x, y, coefficient)
            except ValueError:
                return -np.ones(7)

        def objective(raw: np.ndarray) -> float:
            nonlocal evaluations, improvements, best, best_value, best_vector, suspected_failures
            if evaluations >= task["max_evals"]:
                raise SearchBudget("objective evaluation budget")
            if time.monotonic() >= task["deadline"]:
                raise SearchBudget("global wall deadline")
            evaluations += 1
            try:
                x, y, coefficient = decode(raw, shape)
                a, b, eta, d = coefficient
                determinant = a * d - b * eta
                # Infeasible coefficient trials are penalties, never recorded
                # as evaluations of the theorem's entropy residual.
                if min(coefficient) < 0 or determinant < 0:
                    return float(10.0 + np.sum(np.minimum(coefficient, 0.0) ** 2)
                                 + min(determinant, 0.0) ** 2)
                value = audit_case(x, y, tuple(float(v) for v in coefficient))["residual_nats"]
                margins = constraint_values(x, y, coefficient)
                if margins.min() >= -FEASIBILITY_TOLERANCE:
                    if value < best_value:
                        best = full_record(raw, shape)
                        best_value = value
                        best_vector = raw.copy()
                        improvements += 1
                        write_record("feasible_improvement", best)
                    if value < -1e-9:
                        suspected_failures += 1
                        write_record("suspected_negative_witness", full_record(raw, shape))
                return float(value)
            except (ValueError, np.linalg.LinAlgError):
                return 100.0

        termination, optimizer_success, optimizer_message = "completed", False, ""
        try:
            result = minimize(objective, vector, method="SLSQP",
                              constraints=[{"type": "ineq", "fun": constraints}],
                              options={"maxiter": 250, "ftol": 1e-12, "eps": 1e-7})
            optimizer_success = bool(result.success)
            optimizer_message = str(result.message)
        except SearchBudget as exc:
            termination = str(exc)
        except Exception as exc:
            termination = "worker_exception"
            optimizer_message = repr(exc)

        # Replay the stored best from its raw parameterization rather than
        # trusting the optimizer's success flag or final iterate.
        replay = full_record(best_vector, shape)
        if not replay["feasible"]:
            raise AssertionError("stored candidate lost feasibility")
        completion = {
            "start_id": task["id"], "seed": task["seed"], "shape": list(shape),
            "termination": termination, "optimizer_success": optimizer_success,
            "optimizer_message": optimizer_message, "objective_evaluations": evaluations,
            "improvements": improvements, "suspected_negative_evaluations": suspected_failures,
            "initial_residual_nats": initial["residual_nats"],
            "best": replay, "elapsed_seconds": time.monotonic() - task_start,
            "journal": f"sharpness_journals/{journal_path.name}",
        }
        write_record("completed_start", completion)
    return completion


def run(args) -> dict:
    actual_sha = hashlib.sha256((ROOT / "research/gad-thermal.tex").read_bytes()).hexdigest()
    if actual_sha != SOURCE_SHA256:
        raise ValueError("thermal source hash changed")
    start = time.monotonic()
    deadline = start + args.seconds
    output = args.output.resolve()
    journal_dir = output.parent / "sharpness_journals"
    completion_journal = output.parent / "sharpness_completions.jsonl"
    if output.exists() or journal_dir.exists() or completion_journal.exists():
        raise FileExistsError("research records already exist; use an unused directory, e.g. --output results/run-002/search.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    journal_dir.mkdir()
    seeds = np.random.SeedSequence(args.seed).spawn(args.starts)
    tasks = [{"id": i, "seed": int(seeds[i].generate_state(1)[0]),
              "shape": SHAPES[i % len(SHAPES)], "max_evals": args.max_evals,
              "deadline": deadline, "journal": str(journal_dir / f"start_{i:03}.jsonl")}
             for i in range(args.starts)]
    completed, errors, skipped = [], [], []
    workers = min(args.workers, os.cpu_count() or 1, args.starts)
    dispatched = 0
    with completion_journal.open("x", encoding="utf-8") as ledger:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            pending = {}
            while dispatched < min(workers, len(tasks)):
                task = tasks[dispatched]
                pending[executor.submit(one_start, task)] = task["id"]
                dispatched += 1
            while pending:
                done, _ = wait(pending, timeout=1, return_when=FIRST_COMPLETED)
                for future in done:
                    task_id = pending.pop(future)
                    try:
                        record = future.result()
                        completed.append(record)
                        ledger.write(json.dumps(record, allow_nan=False) + "\n")
                        ledger.flush()
                        print(f"start {task_id:03}: R={record['best']['residual_nats']:.9g}, "
                              f"evals={record['objective_evaluations']}, {record['termination']}", flush=True)
                    except SearchBudget as exc:
                        skipped.append({"start_id": task_id, "reason": str(exc)})
                    except Exception as exc:
                        errors.append({"start_id": task_id, "error": repr(exc)})
                    if dispatched < len(tasks) and time.monotonic() < deadline:
                        task = tasks[dispatched]
                        pending[executor.submit(one_start, task)] = task["id"]
                        dispatched += 1
    completed.sort(key=lambda record: record["start_id"])
    best = min(completed, key=lambda record: record["best"]["residual_nats"]) if completed else None
    report = {
        "schema_version": 1, "experiment": "interior constrained thermal sharpness search",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source": {"commit": UPSTREAM_COMMIT, "thermal_sha256": actual_sha},
        "environment": {"python": platform.python_version(), "numpy": np.__version__,
                        "scipy": scipy.__version__, "platform": platform.system(),
                        "workers": workers, "blas_threads_per_worker": 1},
        "settings": {"seed": args.seed, "requested_starts": args.starts,
                     "maximum_objective_evaluations_per_start": args.max_evals,
                     "wall_budget_seconds": args.seconds,
                     "wall_budget_kind": "cooperative deadline; initialization, constraints and objective checked; process startup/join may add overhead",
                     "coefficient_minimum": MIN_COEFFICIENT,
                     "K_squared_minimum": MIN_DETERMINANT, "u_minimum": MIN_U,
                     "commutator_minimum": MIN_COMMUTATOR,
                     "feasibility_tolerance": FEASIBILITY_TOLERANCE},
        "summary": {"dispatched_starts": dispatched, "completed_starts": len(completed),
                    "worker_errors": len(errors), "deadline_skipped_starts": len(skipped),
                    "wall_seconds": time.monotonic() - start,
                    "objective_evaluations": sum(record["objective_evaluations"] for record in completed),
                    "best_residual_nats": None if best is None else best["best"]["residual_nats"],
                    "best_start_id": None if best is None else best["start_id"],
                    "optimizer_successful_starts": sum(record["optimizer_success"] for record in completed),
                    "evaluation_budget_stops": sum(record["termination"] == "objective evaluation budget" for record in completed),
                    "suspected_negative_evaluations": sum(record["suspected_negative_evaluations"] for record in completed)},
        "interpretation": "Best feasible points found in the stated interior noncommuting subdomain. Budget-stopped runs are not converged minima; equality and boundary tracks are separate.",
        "starts": completed, "errors": errors, "deadline_skipped": skipped,
    }
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if best:
        (output.parent / "sharpness_best.json").write_text(json.dumps(best, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--starts", type=int, default=128)
    parser.add_argument("--workers", type=int, default=24)
    parser.add_argument("--max-evals", type=int, default=1500)
    parser.add_argument("--seconds", type=float, default=480)
    parser.add_argument("--seed", type=int, default=276202610)
    parser.add_argument("--output", type=Path, default=ROOT / "results/sharpness_search.json")
    args = parser.parse_args()
    if not 1 <= args.starts <= 128 or not 1 <= args.workers <= 24:
        parser.error("starts must be 1..128 and workers 1..24")
    if not 10 <= args.max_evals <= 1500 or not 1 <= args.seconds <= 600:
        parser.error("max-evals must be 10..1500 and seconds 1..600")
    try:
        report = run(args)
    except FileExistsError as exc:
        parser.error(str(exc))
    print(json.dumps(report["summary"], indent=2))
    return int(bool(report["errors"]))


if __name__ == "__main__":
    raise SystemExit(main())
