"""Utilities."""
from datetime import datetime
from time import time
from random import randrange


_OFFSET_2022_02_02_MILLI: int = int(
    datetime(year=2022, month=2, day=2).timestamp() * 1000
)
_TENANT_ID_RSHIFT_OFFSET: int = 47


def generate_id(tenant_id: int) -> int:
    """Generate user-specific id to use in DB.

    * Total 64 bits.
    * Assuming 100000 users' data will be stored in a single db instance.
      So `17bits` are needed for user-id

    1. First 17bits user-id.
    2. Next 42bits timestmap diff from 2023-03-03
    3. Next 4bits random number.
    """
    timestamp_offset: int = 5

    timestamp_diff: int = int(time() * 1000) - _OFFSET_2022_02_02_MILLI

    return (
        (tenant_id << _TENANT_ID_RSHIFT_OFFSET)
        + (timestamp_diff << timestamp_offset)
        # 4 bit random number.
        + (randrange(0, (2**4) - 1))
    )
