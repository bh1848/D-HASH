from unittest.mock import patch

from dhash_repro.experiment.runner import run_experiments


def test_run_experiments_pipeline_saves_pipeline_results() -> None:
    with (
        patch("dhash_repro.experiment.runner.resolve_dataset", return_value="nasa"),
        patch(
            "dhash_repro.experiment.runner.load_dataset_workload_base",
            return_value=(["key-a", "key-b", "key-c"], 3),
        ),
        patch(
            "dhash_repro.experiment.runner.run_single_mode",
            return_value=(100.0, 1.0, 2.0, 3.0, 5.0),
        ),
        patch(
            "dhash_repro.experiment.runner.save_to_csv",
        ) as mock_save,
        patch(
            "dhash_repro.experiment.runner.reset_np_rng",
        ),
        patch(
            "dhash_repro.experiment.runner.generate_zipf_workload",
            return_value=["key-a", "key-b"],
        ),
        patch("os.makedirs"),
    ):
        run_experiments(mode="pipeline", alpha=1.5, repeats=1)

    assert mock_save.call_count >= 1
    assert any("pipeline" in call.args[1] for call in mock_save.call_args_list)


def test_run_experiments_zipf_saves_zipf_results() -> None:
    with (
        patch("dhash_repro.experiment.runner.resolve_dataset", return_value="nasa"),
        patch(
            "dhash_repro.experiment.runner.load_dataset_workload_base",
            return_value=(["key-a", "key-b", "key-c"], 3),
        ),
        patch(
            "dhash_repro.experiment.runner.run_single_mode",
            return_value=(100.0, 1.0, 2.0, 3.0, 5.0),
        ),
        patch(
            "dhash_repro.experiment.runner.save_to_csv",
        ) as mock_save,
        patch(
            "dhash_repro.experiment.runner.reset_np_rng",
        ),
        patch(
            "dhash_repro.experiment.runner.generate_zipf_workload",
            return_value=["key-a", "key-b"],
        ),
        patch("os.makedirs"),
    ):
        run_experiments(mode="zipf", alpha=1.5, repeats=1)

    assert mock_save.call_count >= 1
    assert any("zipf" in call.args[1] for call in mock_save.call_args_list)


def test_run_experiments_ablation_saves_ablation_results() -> None:
    with (
        patch("dhash_repro.experiment.runner.resolve_dataset", return_value="nasa"),
        patch(
            "dhash_repro.experiment.runner.load_dataset_workload_base",
            return_value=(["key-a", "key-b", "key-c"], 3),
        ),
        patch(
            "dhash_repro.experiment.runner.run_single_mode",
            return_value=(100.0, 1.0, 2.0, 3.0, 5.0),
        ),
        patch(
            "dhash_repro.experiment.runner.save_to_csv",
        ) as mock_save,
        patch(
            "dhash_repro.experiment.runner.reset_np_rng",
        ),
        patch(
            "dhash_repro.experiment.runner.generate_zipf_workload",
            return_value=["key-a", "key-b"],
        ),
        patch("os.makedirs"),
    ):
        run_experiments(mode="ablation", alpha=1.5, repeats=1)

    assert mock_save.call_count >= 1
    assert any("ablation" in call.args[1] for call in mock_save.call_args_list)


def test_run_experiments_all_calls_run_single_mode_multiple_times() -> None:
    with (
        patch("dhash_repro.experiment.runner.resolve_dataset", return_value="nasa"),
        patch(
            "dhash_repro.experiment.runner.load_dataset_workload_base",
            return_value=(["key-a", "key-b", "key-c"], 3),
        ),
        patch(
            "dhash_repro.experiment.runner.run_single_mode",
            return_value=(100.0, 1.0, 2.0, 3.0, 5.0),
        ) as mock_run_single_mode,
        patch(
            "dhash_repro.experiment.runner.save_to_csv",
        ),
        patch(
            "dhash_repro.experiment.runner.reset_np_rng",
        ),
        patch(
            "dhash_repro.experiment.runner.generate_zipf_workload",
            return_value=["key-a", "key-b"],
        ),
        patch("os.makedirs"),
    ):
        run_experiments(mode="all", alpha=1.5, repeats=1)

    assert mock_run_single_mode.call_count > 1
