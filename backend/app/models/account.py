from sqlalchemy import (
    Boolean, Column, Integer, String,
    Enum, ForeignKey, Table,
)
from sqlalchemy.orm import relationship
from sqlalchemy.future import select
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from extra.enums import Roles, RegistrationTypes, SocialTypes
from db.model import Model
from db.mixins import TimestampsMixin
from core.security import get_password_hash, verify_password


account_role = Table(
    'account_role',
    Model.metadata,
    Column('account_id', Integer, ForeignKey('account.id', ondelete='CASCADE')),
    Column('role_id', Integer, ForeignKey('role.id', ondelete='CASCADE')),
)


class Account(Model, TimestampsMixin):
    __repr_attrs__ = ['email']

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(50), index=True, nullable=True)
    email = Column(String(200), unique=True, index=True, nullable=True)
    phone = Column(String(200), unique=True, index=True, nullable=True)

    auths = relationship('AuthorizationData',
                         back_populates='account',
                         cascade='all, delete',
                         passive_deletes=True)
    roles = relationship('Role',
                         secondary=account_role,
                         back_populates='accounts',
                         lazy='joined',
                         cascade='all, delete')

    __mapper_args__ = {"eager_defaults": True}

    @classmethod
    async def create(
        cls,
        db,
        password: str,
        role: Roles = Roles.customer,
        registration_type: RegistrationTypes = RegistrationTypes.forms,
        social_type=None,
        external_id=None,
        **fields
    ):
        role = await select(Role).filter_by(name=role).scalar_one(db)
        account = await cls(roles=[role], **fields).save(db)
        auth_data = await AuthorizationData(
            login=fields.get('email') or fields.get('phone'),
            password=password,
            registration_type=registration_type,
            account_id=account.id,
        ).save(db)

        if registration_type == RegistrationTypes.social:
            await SocialIntegration(
                social_type=social_type,
                external_id=external_id,
                auth_data_id=auth_data.id,
            ).save(db)

        return account


class Role(Model):
    __repr_attrs__ = ['guid']

    id = Column(Integer, primary_key=True, index=True)
    guid = Column(String(100), unique=True, index=True)
    name = Column(Enum(Roles, length=100), unique=True, nullable=False, index=True)

    accounts = relationship('Account',
                            secondary=account_role,
                            back_populates='roles',
                            passive_deletes=True)


class AuthorizationData(Model):
    __tablename__ = 'auth_data'
    __repr_attrs__ = ['login']

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(200), index=True)
    _password = Column(String(200))
    registration_type = Column(Enum(RegistrationTypes, length=100), nullable=False, index=True)
    is_active = Column(Boolean(), default=False)

    account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    account = relationship('Account', back_populates='auths')
    socials = relationship('SocialIntegration',
                           back_populates='auth_data',
                           cascade='all, delete',
                           passive_deletes=True)

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
    __tablename__ = 'socials'

    id = Column(Integer, primary_key=True, index=True)
    social_type = Column(Enum(SocialTypes, length=100), nullable=False, index=True)

    # user id in social service
    external_id = Column(String(100), index=True)

    auth_data_id = Column(Integer, ForeignKey('auth_data.id', ondelete='CASCADE'), nullable=False)
    auth_data = relationship('AuthorizationData', back_populates='socials')
