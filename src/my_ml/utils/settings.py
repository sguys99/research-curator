import os
import random

import numpy as np
import torch


def set_random_seed(
    random_seed: int = 42,
    use_torch: bool = False,
):
    """
    Set a global random seed for reproducibility across various libraries.

    Args:
        random_seed (int): Seed value to be set.
        use_torch (bool): Whether to set seed for PyTorch or not.
    """
    os.environ["PYTHONHASHSEED"] = str(random_seed)
    random.seed(random_seed)
    np.random.seed(random_seed)

    if use_torch:
        torch.manual_seed(random_seed)
        torch.cuda.manual_seed(random_seed)
        torch.cuda.manual_seed_all(random_seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
