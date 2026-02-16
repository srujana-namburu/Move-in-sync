"""
Comprehensive Evaluation Suite for MoveInSync AI Agent
Measures tool selection accuracy, entity extraction, HITL behavior, and regression detection.
"""
import sys
import os
import asyncio
import json
import time
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

# Path setup
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_PATH = os.path.join(PROJECT_ROOT, "backend")
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, BACKEND_PATH)

# Import aliasing
import importlib

def alias(name: str, real_name: str):
    try:
        module = importlib.import_module(real_name)
        sys.modules[name] = module
    except Exception:
        pass

alias("models", "backend.models")
alias("database", "backend.database")
alias("crud", "backend.crud")
alias("routes", "backend.routes")
alias("Agents", "backend.Agents")

# Import agent
try:
    from backend.Agents.graph import app as agent_graph
    from backend.Agents.state import MoviState
except Exception as e:
    print(f"❌ Cannot import agent: {e}")
    agent_graph = None


@dataclass
class EvalResult:
    """Single evaluation result"""
    test_id: str
    passed: bool
    category: str
    expected_tool: Optional[str] = None
    predicted_tool: Optional[str] = None
    expected_entities: Optional[Dict] = None
    predicted_entities: Optional[Dict] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    hitl_triggered: bool = False
    expected_hitl: bool = False


@dataclass
class EvalMetrics:
    """Aggregated evaluation metrics"""
    total_tests: int
    passed_tests: int
    failed_tests: int

    # Tool selection metrics
    tool_selection_accuracy: float
    tool_selection_correct: int
    tool_selection_total: int

    # Entity extraction metrics
    entity_extraction_accuracy: float
    entity_extraction_correct: int
    entity_extraction_total: int

    # HITL metrics
    hitl_accuracy: float
    hitl_correct: int
    hitl_total: int

    # Performance metrics
    avg_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float

    # Category breakdowns
    category_scores: Dict[str, float]

    # Overall score
    overall_accuracy: float

    def to_dict(self) -> Dict:
        return asdict(self)


class MoviEvaluator:
    """Comprehensive evaluator for Movi AI agent"""

    def __init__(self, dataset_path: str = "evals/dataset.json", baseline_path: str = "evals/baseline.json"):
        self.dataset_path = dataset_path
        self.baseline_path = baseline_path
        self.dataset = self._load_dataset()
        self.baseline = self._load_baseline()
        self.results: List[EvalResult] = []

    def _load_dataset(self) -> Dict:
        """Load evaluation dataset"""
        try:
            with open(self.dataset_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Dataset not found at {self.dataset_path}")
            return {}

    def _load_baseline(self) -> Optional[Dict]:
        """Load baseline metrics for regression detection"""
        try:
            with open(self.baseline_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ℹ️  No baseline found at {self.baseline_path}")
            return None

    def _save_baseline(self, metrics: EvalMetrics):
        """Save current metrics as new baseline"""
        with open(self.baseline_path, 'w') as f:
            json.dump(metrics.to_dict(), f, indent=2)
        print(f"✅ Baseline saved to {self.baseline_path}")

    async def _run_agent(self, user_msg: str, context_page: str = "buses") -> Tuple[Optional[str], Optional[Dict], bool, float]:
        """
        Run agent and extract predicted tool, entities, and HITL status
        Returns: (tool_name, entities, hitl_triggered, latency_ms)
        """
        if agent_graph is None:
            return None, None, False, 0.0

        session_id = f"eval-{int(time.time() * 1000)}"
        config = {"configurable": {"thread_id": session_id}}

        input_data = {
            "user_msg": user_msg,
            "current_page": context_page,
            "messages": [],
            "image_base64": None,
            "image_content": None,
            "intent": None,
            "tool_name": None,
            "entities": None,
            "needs_user_input": False,
            "consequences": None,
            "awaiting_confirmation": False,
            "tool_result": None
        }

        start_time = time.time()

        try:
            # Run the graph
            result = await agent_graph.ainvoke(input_data, config=config)

            latency_ms = (time.time() - start_time) * 1000

            # Extract results
            tool_name = result.get("tool_name")
            entities = result.get("entities", {})

            # Check if HITL was triggered (check graph state)
            state = agent_graph.get_state(config)
            hitl_triggered = bool(state.next)  # If next is not empty, we're interrupted

            return tool_name, entities, hitl_triggered, latency_ms

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            print(f"⚠️  Agent error: {e}")
            return None, None, False, latency_ms

    def _compare_entities(self, expected: Dict, predicted: Optional[Dict]) -> bool:
        """Compare expected vs predicted entities (fuzzy match)"""
        if predicted is None:
            return len(expected) == 0

        if len(expected) == 0:
            return True

        # Check if all expected keys exist and values are similar
        matched = 0
        for key, expected_val in expected.items():
            if key in predicted:
                pred_val = str(predicted[key]).lower().strip()
                exp_val = str(expected_val).lower().strip()

                # Fuzzy match (contains or exact)
                if exp_val in pred_val or pred_val in exp_val or exp_val == pred_val:
                    matched += 1

        # Consider it a match if >= 70% of entities match
        return (matched / len(expected)) >= 0.7

    async def evaluate_tool_selection(self) -> List[EvalResult]:
        """Evaluate tool selection accuracy"""
        results = []
        test_cases = self.dataset.get("tool_selection", [])

        print(f"\n🔧 Testing Tool Selection ({len(test_cases)} cases)...")

        for idx, test in enumerate(test_cases, 1):
            test_id = test["id"]
            user_input = test["input"]
            expected_tool = test["expected_tool"]
            expected_entities = test.get("expected_entities", {})
            expected_hitl = test.get("requires_hitl", False)
            context_page = test.get("context_page", "buses")
            category = test.get("category", "unknown")

            # Run agent
            predicted_tool, predicted_entities, hitl_triggered, latency = await self._run_agent(
                user_input, context_page
            )

            # Check tool match
            tool_correct = predicted_tool == expected_tool

            # Check entity match
            entities_correct = self._compare_entities(expected_entities, predicted_entities)

            # Check HITL
            hitl_correct = hitl_triggered == expected_hitl

            # Overall pass
            passed = tool_correct and entities_correct and hitl_correct

            result = EvalResult(
                test_id=test_id,
                passed=passed,
                category=category,
                expected_tool=expected_tool,
                predicted_tool=predicted_tool,
                expected_entities=expected_entities,
                predicted_entities=predicted_entities,
                latency_ms=latency,
                hitl_triggered=hitl_triggered,
                expected_hitl=expected_hitl,
                error=None if passed else f"Tool: {tool_correct}, Entities: {entities_correct}, HITL: {hitl_correct}"
            )

            results.append(result)

            # Print progress
            status = "✅" if passed else "❌"
            print(f"  {status} {idx}/{len(test_cases)}: {test_id} - {user_input[:50]}...")
            if not passed:
                print(f"     Expected: {expected_tool}, Got: {predicted_tool}")

        return results

    async def evaluate_context_awareness(self) -> List[EvalResult]:
        """Evaluate context-aware tool selection"""
        results = []
        test_cases = self.dataset.get("context_awareness", [])

        print(f"\n🎯 Testing Context Awareness ({len(test_cases)} cases)...")

        for idx, test in enumerate(test_cases, 1):
            test_id = test["id"]
            user_input = test["input"]
            context_page = test["context_page"]
            expected_tool = test.get("expected_tool")

            predicted_tool, _, _, latency = await self._run_agent(user_input, context_page)

            passed = predicted_tool == expected_tool

            result = EvalResult(
                test_id=test_id,
                passed=passed,
                category="context",
                expected_tool=expected_tool,
                predicted_tool=predicted_tool,
                latency_ms=latency
            )

            results.append(result)

            status = "✅" if passed else "❌"
            print(f"  {status} {idx}/{len(test_cases)}: {test_id} (page: {context_page})")

        return results

    async def evaluate_hitl(self) -> List[EvalResult]:
        """Evaluate HITL trigger accuracy"""
        results = []
        test_cases = self.dataset.get("hitl_validation", [])

        print(f"\n🛡️  Testing HITL Triggers ({len(test_cases)} cases)...")

        for idx, test in enumerate(test_cases, 1):
            test_id = test["id"]
            user_input = test["input"]
            context_page = test.get("context_page", "buses")
            expected_hitl = test.get("expected_hitl", False)

            _, _, hitl_triggered, latency = await self._run_agent(user_input, context_page)

            passed = hitl_triggered == expected_hitl

            result = EvalResult(
                test_id=test_id,
                passed=passed,
                category="hitl",
                hitl_triggered=hitl_triggered,
                expected_hitl=expected_hitl,
                latency_ms=latency
            )

            results.append(result)

            status = "✅" if passed else "❌"
            print(f"  {status} {idx}/{len(test_cases)}: {test_id} - HITL: {hitl_triggered}")

        return results

    def calculate_metrics(self, results: List[EvalResult]) -> EvalMetrics:
        """Calculate comprehensive metrics from results"""

        if not results:
            return EvalMetrics(
                total_tests=0, passed_tests=0, failed_tests=0,
                tool_selection_accuracy=0.0, tool_selection_correct=0, tool_selection_total=0,
                entity_extraction_accuracy=0.0, entity_extraction_correct=0, entity_extraction_total=0,
                hitl_accuracy=0.0, hitl_correct=0, hitl_total=0,
                avg_latency_ms=0.0, max_latency_ms=0.0, p95_latency_ms=0.0,
                category_scores={}, overall_accuracy=0.0
            )

        total = len(results)
        passed = sum(1 for r in results if r.passed)

        # Tool selection accuracy
        tool_tests = [r for r in results if r.expected_tool is not None]
        tool_correct = sum(1 for r in tool_tests if r.predicted_tool == r.expected_tool)
        tool_accuracy = (tool_correct / len(tool_tests)) * 100 if tool_tests else 0.0

        # Entity extraction accuracy
        entity_tests = [r for r in results if r.expected_entities]
        entity_correct = sum(1 for r in entity_tests if r.passed)
        entity_accuracy = (entity_correct / len(entity_tests)) * 100 if entity_tests else 0.0

        # HITL accuracy
        hitl_tests = [r for r in results if r.expected_hitl is not None]
        hitl_correct = sum(1 for r in hitl_tests if r.hitl_triggered == r.expected_hitl)
        hitl_accuracy = (hitl_correct / len(hitl_tests)) * 100 if hitl_tests else 0.0

        # Latency metrics
        latencies = [r.latency_ms for r in results if r.latency_ms]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        max_latency = max(latencies) if latencies else 0.0
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0.0

        # Category breakdown
        categories = {}
        for result in results:
            cat = result.category
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result.passed:
                categories[cat]["passed"] += 1

        category_scores = {
            cat: (stats["passed"] / stats["total"]) * 100
            for cat, stats in categories.items()
        }

        # Overall accuracy
        overall = (passed / total) * 100 if total > 0 else 0.0

        return EvalMetrics(
            total_tests=total,
            passed_tests=passed,
            failed_tests=total - passed,
            tool_selection_accuracy=tool_accuracy,
            tool_selection_correct=tool_correct,
            tool_selection_total=len(tool_tests),
            entity_extraction_accuracy=entity_accuracy,
            entity_extraction_correct=entity_correct,
            entity_extraction_total=len(entity_tests),
            hitl_accuracy=hitl_accuracy,
            hitl_correct=hitl_correct,
            hitl_total=len(hitl_tests),
            avg_latency_ms=avg_latency,
            max_latency_ms=max_latency,
            p95_latency_ms=p95_latency,
            category_scores=category_scores,
            overall_accuracy=overall
        )

    def check_regression(self, current_metrics: EvalMetrics) -> Tuple[bool, List[str]]:
        """Check if metrics regressed compared to baseline"""
        if not self.baseline:
            print("ℹ️  No baseline found, skipping regression check")
            return True, []

        regressions = []

        # Define thresholds
        REGRESSION_THRESHOLD = 5.0  # 5% drop is considered regression

        baseline_overall = self.baseline.get("overall_accuracy", 0)
        if current_metrics.overall_accuracy < baseline_overall - REGRESSION_THRESHOLD:
            regressions.append(
                f"Overall accuracy regressed: {baseline_overall:.1f}% → {current_metrics.overall_accuracy:.1f}%"
            )

        baseline_tool = self.baseline.get("tool_selection_accuracy", 0)
        if current_metrics.tool_selection_accuracy < baseline_tool - REGRESSION_THRESHOLD:
            regressions.append(
                f"Tool selection regressed: {baseline_tool:.1f}% → {current_metrics.tool_selection_accuracy:.1f}%"
            )

        baseline_entity = self.baseline.get("entity_extraction_accuracy", 0)
        if current_metrics.entity_extraction_accuracy < baseline_entity - REGRESSION_THRESHOLD:
            regressions.append(
                f"Entity extraction regressed: {baseline_entity:.1f}% → {current_metrics.entity_extraction_accuracy:.1f}%"
            )

        baseline_hitl = self.baseline.get("hitl_accuracy", 0)
        if current_metrics.hitl_accuracy < baseline_hitl - REGRESSION_THRESHOLD:
            regressions.append(
                f"HITL accuracy regressed: {baseline_hitl:.1f}% → {current_metrics.hitl_accuracy:.1f}%"
            )

        return len(regressions) == 0, regressions

    def print_report(self, metrics: EvalMetrics, regressions: List[str]):
        """Print comprehensive evaluation report"""
        print("\n" + "="*70)
        print("📊 MOVEINSYNC AI AGENT EVALUATION REPORT")
        print("="*70)

        print(f"\n📈 OVERALL METRICS")
        print(f"  Total Tests:        {metrics.total_tests}")
        print(f"  Passed:             {metrics.passed_tests} ({metrics.overall_accuracy:.1f}%)")
        print(f"  Failed:             {metrics.failed_tests}")

        print(f"\n🎯 TOOL SELECTION")
        print(f"  Accuracy:           {metrics.tool_selection_accuracy:.1f}%")
        print(f"  Correct:            {metrics.tool_selection_correct}/{metrics.tool_selection_total}")

        print(f"\n🔍 ENTITY EXTRACTION")
        print(f"  Accuracy:           {metrics.entity_extraction_accuracy:.1f}%")
        print(f"  Correct:            {metrics.entity_extraction_correct}/{metrics.entity_extraction_total}")

        print(f"\n🛡️  HITL BEHAVIOR")
        print(f"  Accuracy:           {metrics.hitl_accuracy:.1f}%")
        print(f"  Correct:            {metrics.hitl_correct}/{metrics.hitl_total}")

        print(f"\n⚡ PERFORMANCE")
        print(f"  Avg Latency:        {metrics.avg_latency_ms:.0f}ms")
        print(f"  Max Latency:        {metrics.max_latency_ms:.0f}ms")
        print(f"  P95 Latency:        {metrics.p95_latency_ms:.0f}ms")

        print(f"\n📂 CATEGORY BREAKDOWN")
        for category, score in sorted(metrics.category_scores.items()):
            print(f"  {category:20s}: {score:.1f}%")

        # Regression check
        if regressions:
            print(f"\n⚠️  REGRESSIONS DETECTED:")
            for reg in regressions:
                print(f"  ❌ {reg}")
        else:
            print(f"\n✅ No regressions detected")

        print("\n" + "="*70)

        # Pass/Fail threshold
        if metrics.overall_accuracy >= 85.0 and not regressions:
            print("✅ EVALUATION PASSED (>= 85% accuracy, no regressions)")
            return 0
        else:
            print("❌ EVALUATION FAILED (< 85% accuracy or regressions detected)")
            return 1

    async def run_full_evaluation(self, save_baseline: bool = False) -> int:
        """Run complete evaluation suite"""
        print("🚀 Starting MoveInSync AI Agent Evaluation\n")
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"📁 Dataset: {self.dataset_path}")

        all_results = []

        # Run all evaluation categories
        all_results.extend(await self.evaluate_tool_selection())
        all_results.extend(await self.evaluate_context_awareness())
        all_results.extend(await self.evaluate_hitl())

        # Calculate metrics
        metrics = self.calculate_metrics(all_results)

        # Check regressions
        passed, regressions = self.check_regression(metrics)

        # Print report
        exit_code = self.print_report(metrics, regressions)

        # Save results
        results_file = f"evals/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics.to_dict(),
                "results": [asdict(r) for r in all_results],
                "regressions": regressions
            }, f, indent=2)
        print(f"\n💾 Results saved to {results_file}")

        # Save new baseline if requested
        if save_baseline:
            self._save_baseline(metrics)

        return exit_code


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="MoveInSync AI Agent Evaluation Suite")
    parser.add_argument("--dataset", default="evals/dataset.json", help="Path to eval dataset")
    parser.add_argument("--baseline", default="evals/baseline.json", help="Path to baseline metrics")
    parser.add_argument("--save-baseline", action="store_true", help="Save current run as new baseline")

    args = parser.parse_args()

    evaluator = MoviEvaluator(dataset_path=args.dataset, baseline_path=args.baseline)
    exit_code = await evaluator.run_full_evaluation(save_baseline=args.save_baseline)

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
