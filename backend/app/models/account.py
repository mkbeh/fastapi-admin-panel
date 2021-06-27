from sqlalchemy import (
    Boolean, Column, Integer, String,
    Enum, ForeignKey, Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from extra.enums import Roles, RegistrationTypes, SocialTypes
from db.model import Model
from db.mixins import TimestampMixin
from core.security import get_password_hash, verify_password


account_role = Table(
    'account_role',
    Model.metadata,
    Column('account_id', Integer, ForeignKey('account.id')),
    Column('role_id', Integer, ForeignKey('role.id')),
)


class Account(TimestampMixin, Model):
    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(50), index=True, nullable=True)
    email = Column(String(200), unique=True, index=True, nullable=True)
    phone = Column(String(200), unique=True, index=True, nullable=True)

    auths = relationship('AuthorizationData', back_populates='account')
    roles = relationship('Role',
                         secondary=account_role,
                         back_populates='accounts',
                         lazy='joined')

    __mapper_args__ = {"eager_defaults": True}


class Role(Model):
    id = Column(Integer, primary_key=True, index=True)
    guid = Column(String(100), unique=True, index=True)
    name = Column(Enum(Roles, length=100), unique=True, nullable=False, index=True)

    accounts = relationship('Account',
                            secondary=account_role,
                            back_populates='roles')


class AuthorizationData(Model):
    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(200), index=True)
    _password = Column(String(200))
    registration_type = Column(Enum(RegistrationTypes, length=100), nullable=False, index=True)
    is_active = Column(Boolean(), default=True)

    account_id = Column(Integer, ForeignKey('account.id'), nullable=False)
    account = relationship('Account', back_populates='auths')

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = get_password_hash(password)

    @hybrid_method
    def verify_password(self, password):
        return verify_password(password, self._password)


class SocialIntegration(Model):
    id = Column(Integer, primary_key=True, index=True)
    social_type = Column(Enum(SocialTypes, length=100), nullable=False, index=True)

    # user id in social service
    external_id = Column(String(100), index=True)
