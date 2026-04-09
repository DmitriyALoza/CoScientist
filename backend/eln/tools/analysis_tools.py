"""Analysis tools for data processing and statistical computation."""

import json

from langchain_core.tools import tool

# Safe builtins for run_python_analysis sandbox
_SAFE_BUILTINS = {
    "__import__": __import__,
    "print": print,
    "range": range,
    "len": len,
    "list": list,
    "dict": dict,
    "str": str,
    "int": int,
    "float": float,
    "round": round,
    "zip": zip,
    "enumerate": enumerate,
    "sorted": sorted,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "isinstance": isinstance,
    "type": type,
    "bool": bool,
    "tuple": tuple,
    "set": set,
    "repr": repr,
}


@tool
def run_python_analysis(code: str, data_path: str = "", save_plot: str = "") -> str:
    """Run sandboxed Python analysis on artifact data.

    Executes Python code with numpy, pandas, scipy, matplotlib, seaborn,
    statsmodels, and pingouin available. Can save plots as artifacts.

    Args:
        code: Python code to execute. Use 'data' variable for loaded data.
              Use plt.savefig(plot_path) to save a plot (plot_path is injected).
        data_path: Path to a CSV or JSON artifact file to load as 'data'.
        save_plot: If provided, saves the current matplotlib figure to
                   artifacts/{save_plot} after execution.

    Returns:
        stdout output, plot save confirmation, or error message.
    """
    import io
    import sys
    from contextlib import redirect_stdout
    from pathlib import Path

    namespace: dict = {"__builtins__": _SAFE_BUILTINS}

    # Load data if provided
    if data_path:
        p = Path(data_path)
        if not p.exists():
            return f"File not found: {data_path}"
        try:
            if p.suffix == ".csv":
                import pandas as pd
                namespace["data"] = pd.read_csv(p)
            elif p.suffix == ".json":
                with open(p) as f:
                    namespace["data"] = json.load(f)
            else:
                namespace["data"] = p.read_text()
        except Exception as e:
            return f"Error loading data: {e}"

    # Add analysis modules
    try:
        import math
        import numpy as np
        import pandas as pd
        namespace.update({"np": np, "pd": pd, "math": math})
    except ImportError:
        pass

    try:
        import scipy.stats as stats
        namespace["stats"] = stats
    except ImportError:
        pass

    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use("Agg")
        import seaborn as sns
        namespace.update({"plt": plt, "sns": sns})
    except ImportError:
        pass

    try:
        import statsmodels.api as sm
        namespace["sm"] = sm
    except ImportError:
        pass

    try:
        import pingouin as pg
        namespace["pg"] = pg
    except ImportError:
        pass

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            exec(code, namespace)  # noqa: S102
        output = buf.getvalue() or "Execution completed (no output)."

        # Save plot if requested
        if save_plot:
            try:
                import matplotlib.pyplot as plt
                from eln.tools.file_tools import get_run_path
                run_path = get_run_path()
                plot_path = run_path / "artifacts" / save_plot
                plot_path.parent.mkdir(parents=True, exist_ok=True)
                plt.savefig(str(plot_path), bbox_inches="tight", dpi=150)
                plt.close()
                output += f"\nPlot saved: {plot_path}"
            except Exception as e:
                output += f"\nError saving plot: {e}"

        return output
    except Exception as e:
        return f"Execution error: {type(e).__name__}: {e}"


@tool
def compute_statistics(data_json: str, test_type: str = "descriptive") -> str:
    """Compute statistics on a dataset.

    Args:
        data_json: JSON array of numbers or {group: [values]} dict for group comparisons.
        test_type: One of:
            'descriptive' — mean, stdev, min, max, median
            't_test'      — independent samples t-test (2 groups)
            'paired_t_test' — paired t-test (before/after, same subjects)
            'anova'       — one-way ANOVA (3+ groups)
            'mann_whitney' — non-parametric 2-group test
            'kruskal'     — non-parametric multi-group test
            'pearson'     — Pearson correlation (2 arrays)
            'spearman'    — Spearman correlation (2 arrays)
            'fold_change' — log2 fold change (2 groups: control, treatment)
            'effect_size' — Cohen's d and eta-squared (requires pingouin)

    Returns:
        Statistical summary as formatted text.
    """
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError as e:
        return f"Invalid JSON: {e}"

    try:
        import statistics as _stats

        from scipy import stats

        if test_type == "descriptive":
            if isinstance(data, list):
                values = [float(x) for x in data]
                return (
                    f"N: {len(values)}\n"
                    f"Mean: {_stats.mean(values):.4f}\n"
                    f"Stdev: {_stats.stdev(values):.4f}\n"
                    f"Min: {min(values):.4f}\n"
                    f"Max: {max(values):.4f}\n"
                    f"Median: {_stats.median(values):.4f}"
                )
            return "For descriptive stats, provide a JSON array of numbers."

        elif test_type == "t_test":
            if not isinstance(data, dict) or len(data) < 2:
                return "t_test requires a dict with exactly 2 groups: {'group1': [...], 'group2': [...]}"
            groups = list(data.values())
            t_stat, p_val = stats.ttest_ind(groups[0], groups[1])
            return (
                f"Independent t-test\n"
                f"t-statistic: {t_stat:.4f}\n"
                f"p-value: {p_val:.4f}\n"
                f"{'Significant' if p_val < 0.05 else 'Not significant'} at α=0.05"
            )

        elif test_type == "paired_t_test":
            if not isinstance(data, dict) or len(data) < 2:
                return "paired_t_test requires {'before': [...], 'after': [...]}"
            groups = list(data.values())
            t_stat, p_val = stats.ttest_rel(groups[0], groups[1])
            return (
                f"Paired t-test\n"
                f"t-statistic: {t_stat:.4f}\n"
                f"p-value: {p_val:.4f}\n"
                f"{'Significant' if p_val < 0.05 else 'Not significant'} at α=0.05"
            )

        elif test_type == "anova":
            if not isinstance(data, dict):
                return "ANOVA requires a dict of groups: {'group1': [...], ...}"
            groups = list(data.values())
            f_stat, p_val = stats.f_oneway(*groups)
            return (
                f"One-way ANOVA\n"
                f"F-statistic: {f_stat:.4f}\n"
                f"p-value: {p_val:.4f}\n"
                f"{'Significant' if p_val < 0.05 else 'Not significant'} at α=0.05"
            )

        elif test_type == "mann_whitney":
            if not isinstance(data, dict) or len(data) < 2:
                return "mann_whitney requires {'group1': [...], 'group2': [...]}"
            groups = list(data.values())
            u_stat, p_val = stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
            return (
                f"Mann-Whitney U test (non-parametric)\n"
                f"U-statistic: {u_stat:.4f}\n"
                f"p-value: {p_val:.4f}\n"
                f"{'Significant' if p_val < 0.05 else 'Not significant'} at α=0.05"
            )

        elif test_type == "kruskal":
            if not isinstance(data, dict):
                return "kruskal requires a dict of groups: {'group1': [...], ...}"
            groups = list(data.values())
            h_stat, p_val = stats.kruskal(*groups)
            return (
                f"Kruskal-Wallis test (non-parametric multi-group)\n"
                f"H-statistic: {h_stat:.4f}\n"
                f"p-value: {p_val:.4f}\n"
                f"{'Significant' if p_val < 0.05 else 'Not significant'} at α=0.05"
            )

        elif test_type == "pearson":
            if not isinstance(data, dict) or len(data) < 2:
                return "pearson requires {'x': [...], 'y': [...]}"
            arrays = list(data.values())
            r, p_val = stats.pearsonr(arrays[0], arrays[1])
            return (
                f"Pearson correlation\n"
                f"r: {r:.4f}\n"
                f"p-value: {p_val:.4f}\n"
                f"{'Significant' if p_val < 0.05 else 'Not significant'} at α=0.05"
            )

        elif test_type == "spearman":
            if not isinstance(data, dict) or len(data) < 2:
                return "spearman requires {'x': [...], 'y': [...]}"
            arrays = list(data.values())
            rho, p_val = stats.spearmanr(arrays[0], arrays[1])
            return (
                f"Spearman correlation\n"
                f"rho: {rho:.4f}\n"
                f"p-value: {p_val:.4f}\n"
                f"{'Significant' if p_val < 0.05 else 'Not significant'} at α=0.05"
            )

        elif test_type == "fold_change":
            if not isinstance(data, dict) or len(data) < 2:
                return "fold_change requires {'control': [...], 'treatment': [...]}"
            import numpy as np
            groups = list(data.values())
            ctrl_mean = float(np.mean(groups[0]))
            treat_mean = float(np.mean(groups[1]))
            if ctrl_mean == 0:
                return "Cannot compute fold change: control mean is 0."
            raw_fc = treat_mean / ctrl_mean
            log2_fc = float(np.log2(raw_fc))
            direction = "up-regulated" if log2_fc > 0 else "down-regulated"
            return (
                f"Fold Change Analysis\n"
                f"Control mean: {ctrl_mean:.4f}\n"
                f"Treatment mean: {treat_mean:.4f}\n"
                f"Raw fold change: {raw_fc:.4f}x\n"
                f"Log2 fold change: {log2_fc:.4f}\n"
                f"Direction: {direction}"
            )

        elif test_type == "effect_size":
            try:
                import pingouin as pg
            except ImportError:
                return "effect_size requires pingouin: uv add pingouin"
            if not isinstance(data, dict) or len(data) < 2:
                return "effect_size requires {'group1': [...], 'group2': [...]}"
            import numpy as np
            groups = list(data.values())
            g1, g2 = np.array(groups[0], dtype=float), np.array(groups[1], dtype=float)
            cohens_d = pg.compute_effsize(g1, g2, eftype="cohen")
            # eta-squared approximation from t-test
            t_stat, _ = stats.ttest_ind(g1, g2)
            n1, n2 = len(g1), len(g2)
            eta_sq = t_stat**2 / (t_stat**2 + n1 + n2 - 2)
            return (
                f"Effect Size\n"
                f"Cohen's d: {cohens_d:.4f} "
                f"({'large' if abs(cohens_d) >= 0.8 else 'medium' if abs(cohens_d) >= 0.5 else 'small'})\n"
                f"Eta-squared: {eta_sq:.4f} "
                f"({'large' if eta_sq >= 0.14 else 'medium' if eta_sq >= 0.06 else 'small'})"
            )

        else:
            return (
                f"Unknown test_type: {test_type!r}. "
                "Use: 'descriptive', 't_test', 'paired_t_test', 'anova', "
                "'mann_whitney', 'kruskal', 'pearson', 'spearman', 'fold_change', 'effect_size'."
            )

    except ImportError as e:
        return f"Missing dependency: {e}"
    except Exception as e:
        return f"Statistical error: {e}"


@tool
def run_r_analysis(code: str, data_path: str = "") -> str:
    """Run R code via Rscript subprocess.

    R must be installed in the current environment (Rscript on PATH).
    Returns a clear error if R is not available — does not crash.

    Use for: DESeq2, limma, lme4, survival analysis, Seurat, emmeans,
    mixed models, and other R-native bioinformatics workflows.

    Args:
        code: R code to execute. If data_path is provided, 'data' variable
              is pre-loaded as a data.frame from the CSV.
        data_path: Optional path to a CSV artifact to load as 'data'.

    Returns:
        Combined stdout + stderr, or informative error if Rscript not found.
    """
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    from eln.config import settings

    if not settings.r_analysis_enabled:
        return (
            "R analysis is a premium feature (r_analysis_enabled=False). "
            "To enable: set R_ANALYSIS_ENABLED=true in your environment and "
            "ensure R is installed. Python alternatives are available via "
            "run_python_analysis (statsmodels, pingouin, scipy)."
        )

    if not shutil.which("Rscript"):
        return (
            "R is not installed or Rscript is not on PATH. "
            "To enable R analysis: install R (https://www.r-project.org) or "
            "uncomment the R install line in the Dockerfile and rebuild."
        )

    preamble = f'data <- read.csv("{data_path}")\n' if data_path else ""
    full_code = preamble + code

    with tempfile.NamedTemporaryFile(suffix=".R", mode="w", delete=False) as f:
        f.write(full_code)
        tmp_path = f.name

    try:
        result = subprocess.run(
            ["Rscript", "--vanilla", tmp_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout
        if result.stderr.strip():
            output += f"\n[stderr]\n{result.stderr}"
        return output or "R script completed with no output."
    except subprocess.TimeoutExpired:
        return "R script timed out after 60 seconds."
    except Exception as e:
        return f"Error running R: {e}"
    finally:
        Path(tmp_path).unlink(missing_ok=True)
