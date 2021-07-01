import inspect
from typing import Mapping, Optional

from sqlalchemy import util
from sqlalchemy.ext.asyncio import AsyncSession


async def async_call(
    self,
    session: AsyncSession,
    method_name: str = '',
    parameters: Optional[Mapping] = None,
    execution_options: Mapping = util.EMPTY_DICT,
):
    result = await session.execute(self, parameters, execution_options)
    result = result.unique()

    method_name = method_name if method_name else inspect.stack()[1][3]
    if row_method := getattr(result, method_name, None):
        return row_method()

    raise Exception("Invalid method name.")
