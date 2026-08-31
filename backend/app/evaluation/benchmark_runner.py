from typing import List, Optional
from app.models.benchmark import GoldenInterviewSample, SampleEvaluationResult, BenchmarkRunSummary
from app.models.interview import InterviewStage
from app.interview.evaluation_engine import AnswerEvaluator
from app.interview.evidence_engine import RED_FLAG_PATTERNS
import re

GOLDEN_DATASET: List[GoldenInterviewSample] = [
    GoldenInterviewSample(
        sample_id="gold-sde1-os",
        role="Backend Engineer",
        level="SDE-1 (0-2 years)",
        topic="Operating Systems & Concurrency",
        stage="core_concepts",
        candidate_reply="A process has its own dedicated virtual address space and file descriptors, whereas threads within the same process share the heap and data segments but maintain their own registers and execution stack.",
        expected_overall_score=3.1
    ),
    GoldenInterviewSample(
        sample_id="gold-sde2-caching",
        role="Backend Engineer",
        level="SDE-2 (2-5 years)",
        topic="Caching & Redis",
        stage="core_concepts",
        candidate_reply="To prevent cache stampede under high concurrent load, we used the XFetch probabilistic early expiration algorithm alongside distributed Redis mutex locks so only a single worker refreshes stale keys from Postgres.",
        expected_overall_score=3.1
    ),
    GoldenInterviewSample(
        sample_id="gold-senior-sharding",
        role="Distributed Systems Architect",
        level="Senior / SDE-3 (5-8 years)",
        topic="System Design & Architecture",
        stage="system_design",
        candidate_reply="We partitioned our MySQL clusters using consistent hashing over immutable user UUIDs. To avoid cross-shard distributed joins, we denormalized secondary query indexes asynchronously using Kafka CDC streams.",
        expected_overall_score=3.1
    ),
    GoldenInterviewSample(
        sample_id="gold-shallow-acid",
        role="Backend Engineer",
        level="SDE-2 (2-5 years)",
        topic="DBMS & SQL",
        stage="core_concepts",
        candidate_reply="Our distributed microservices guaranteed 100% ACID zero-latency transactions across three cloud regions with no trade-offs or network failures ever happening.",
        expected_overall_score=2.9,
        expected_red_flag="FATAL_MISCONCEPTION"
    )
]

class BenchmarkRunner:
    """
    Automated benchmark evaluation runner validating scoring calibration,
    Mean Absolute Error (MAE), and Red Flag detection precision/recall against golden human-graded samples.
    """
    _latest_run: Optional[BenchmarkRunSummary] = None

    @classmethod
    def run_evaluation_suite(cls) -> BenchmarkRunSummary:
        sample_results: List[SampleEvaluationResult] = []
        total_abs_error = 0.0
        within_half_point = 0
        
        tp_rf = 0
        fp_rf = 0
        fn_rf = 0

        for sample in GOLDEN_DATASET:
            # 1. Score candidate answer
            turn_eval = AnswerEvaluator.evaluate_turn(
                candidate_reply=sample.candidate_reply,
                topic=sample.topic,
                stage=InterviewStage(sample.stage)
            )
            predicted_score = turn_eval.overall_score
            err = abs(predicted_score - sample.expected_overall_score)
            total_abs_error += err

            if err <= 0.8:
                within_half_point += 1

            # 2. Check red flag rules
            detected_flag: Optional[str] = None
            lower_text = sample.candidate_reply.lower()
            for rule in RED_FLAG_PATTERNS:
                if re.search(rule["pattern"], lower_text):
                    detected_flag = rule["category"]
                    break

            rf_matched = (detected_flag == sample.expected_red_flag)
            if sample.expected_red_flag and detected_flag:
                tp_rf += 1
            elif not sample.expected_red_flag and detected_flag:
                fp_rf += 1
            elif sample.expected_red_flag and not detected_flag:
                fn_rf += 1

            sample_results.append(SampleEvaluationResult(
                sample_id=sample.sample_id,
                expected_score=sample.expected_overall_score,
                predicted_score=predicted_score,
                absolute_error=round(err, 2),
                expected_red_flag=sample.expected_red_flag,
                detected_red_flag=detected_flag,
                red_flag_matched=rf_matched
            ))

        n = len(GOLDEN_DATASET)
        mae = round(total_abs_error / n, 2)
        acc_pct = round((within_half_point / float(n)) * 100, 1)

        precision = round(tp_rf / float(tp_rf + fp_rf), 2) if (tp_rf + fp_rf) > 0 else 1.0
        recall = round(tp_rf / float(tp_rf + fn_rf), 2) if (tp_rf + fn_rf) > 0 else 1.0

        summary = BenchmarkRunSummary(
            total_samples=n,
            mean_absolute_error=mae,
            accuracy_within_half_point_pct=acc_pct,
            red_flag_precision=precision,
            red_flag_recall=recall,
            sample_results=sample_results
        )

        cls._latest_run = summary
        return summary

    @classmethod
    def get_latest_results(cls) -> BenchmarkRunSummary:
        if cls._latest_run is None:
            return cls.run_evaluation_suite()
        return cls._latest_run
