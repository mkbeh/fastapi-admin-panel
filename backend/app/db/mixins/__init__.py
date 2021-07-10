# low-level, tiny mixins. you will rarely want to use them in real world
from .inspection import InspectionMixin

# high-level mixins
from .timestamp import TimestampsMixin
from .crud import CRUDMixin
from .eagerload import EagerLoadMixin
from .repr import ReprMixin
from .smartquery import SmartQueryMixin


# all features combined to one mixin
class AllFeaturesMixin(ReprMixin, CRUDMixin, SmartQueryMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
