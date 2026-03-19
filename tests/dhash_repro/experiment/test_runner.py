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
            "dhash_repro.experiment.runner.run_microbench",
        ) as mock_microbench,
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
    mock_microbench.assert_called_once()


def test_run_experiments_microbench_calls_microbench_runner() -> None:
    with (
        patch("dhash_repro.experiment.runner.resolve_dataset", return_value="nasa"),
        patch(
            "dhash_repro.experiment.runner.load_dataset_workload_base",
            return_value=(["key-a", "key-b", "key-c"], 3),
        ),
        patch(
            "dhash_repro.experiment.runner.run_microbench",
        ) as mock_microbench,
        patch(
            "dhash_repro.experiment.runner.save_to_csv",
        ) as mock_save,
        patch("os.makedirs"),
    ):
        run_experiments(mode="microbench", alpha=1.5, repeats=2)

    mock_microbench.assert_called_once_with("nasa", 2, 200)
    assert any("env_metadata" in call.args[1] for call in mock_save.call_args_list)


def test_run_experiments_redistrib_calls_redistribution_runner() -> None:
    keys = ["key-a", "key-b", "key-c"]
    with (
        patch("dhash_repro.experiment.runner.resolve_dataset", return_value="nasa"),
        patch(
            "dhash_repro.experiment.runner.load_dataset_workload_base",
            return_value=(keys, len(keys)),
        ),
        patch(
            "dhash_repro.experiment.runner.run_redistribution_report",
        ) as mock_redistrib,
        patch(
            "dhash_repro.experiment.runner.save_to_csv",
        ) as mock_save,
        patch("os.makedirs"),
    ):
        run_experiments(mode="redistrib", alpha=1.5, repeats=3)

    mock_redistrib.assert_called_once_with("nasa", keys, 3)
    assert any("env_metadata" in call.args[1] for call in mock_save.call_args_list)


def test_run_experiments_zipf_accepts_custom_alpha_list() -> None:
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
        ) as mock_workload,
        patch("os.makedirs"),
    ):
        run_experiments(mode="zipf", alpha=1.5, repeats=1, zipf_alphas=[1.5])

    assert mock_workload.call_count == 1
    assert any("zipf" in call.args[1] for call in mock_save.call_args_list)
