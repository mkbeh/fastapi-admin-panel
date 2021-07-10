# low-level, tiny mixins. you will rarely want to use them in real world
from .insepction import InspectionMixin

# high-level mixins
from .timestamp import TimestampsMixin
from .repr import ReprMixin
from .crud import CRUDMixin
from .eagerload import EagerLoadMixin


# all features combined to one mixin
class AllFeaturesMixin(ReprMixin, CRUDMixin, EagerLoadMixin):
    __abstract__ = True
    __repr__ = ReprMixin.__repr__
