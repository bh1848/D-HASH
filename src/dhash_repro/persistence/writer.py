import pandas as pd
from typing import Any, Dict, List


def save_to_csv(results: List[Dict[str, Any]], filepath: str) -> None:
    pd.DataFrame(results).to_csv(filepath, index=False)
