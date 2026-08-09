"""NGOpen BDP pipelines.

Reproducible, auditable ETL for the datasets published at benthic.io under
the Benthic Data Protocol. Every pipeline runs from scratch in the complete
absence of data, refreshes on rerun, and resumes after a crash.
"""

__version__ = "1.0.0"

from .config import Config, ConfigError, load_config  # noqa: F401
from .ledger import Ledger, StageTimer  # noqa: F401
from .stages import Context, Outcome, Pipeline, STAGE_NAMES  # noqa: F401
