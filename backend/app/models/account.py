from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime,
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
    __repr_attrs__ = ['email', 'phone']

    id = Column(Integer, primary_key=True, index=True)
    fullname = Column(String(50), index=True, nullable=True)
    email = Column(String(200), unique=True, index=True, nullable=True)
    phone = Column(String(200), unique=True, index=True, nullable=True)

    auths = relationship('AuthorizationData',
                         back_populates='account',
                         lazy='joined',
                         cascade='all, delete',
                         passive_deletes=True)
    roles = relationship('Role',
                         secondary=account_role,
                         back_populates='accounts',
                         lazy='joined',
                         cascade='all, delete')

    __mapper_args__ = {"eager_defaults": True}

    @hybrid_property
    def is_active(self) -> bool:
        return any(a.confirmed_at for a in self.auths)

    @hybrid_method
    def has_role(self, role: Roles) -> bool:
        return role in [r.name for r in self.roles]

    @classmethod
    async def create(
        cls,
        db,
        password: str,
        role: Roles = Roles.customer,
        registration_type: RegistrationTypes = RegistrationTypes.forms,
        social_type=None,
        external_id=None,
        skip_confirmation: bool = False,
        **fields
    ):
        role = await select(Role).filter_by(name=role).scalar_one(db)
        account = await super().create(db=db, roles=[role], **fields)
        auth_data = await AuthorizationData.create(
            db=db,
            login=fields.get('email') or fields.get('phone'),
            password=password,
            registration_type=registration_type,
            confirmed_at=datetime.utcnow() if skip_confirmation else None,
            account_id=account.id,
        )

        if registration_type == RegistrationTypes.social:
            await SocialIntegration.create(
                db=db,
                social_type=social_type,
                external_id=external_id,
                auth_data_id=auth_data.id,
            )

        return account

    async def update(self, db, **fields):
        if fields.get('password'):
            auth_data = await select(AuthorizationData) \
                .filter_by(account_id=self.id) \
                .scalar_one(db)

            await auth_data.update(
                db=db,
                password=get_password_hash(fields.pop('password'))
            )
        return await super().update(db, **fields)


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
    confirmed_at = Column(DateTime, nullable=True)

    account_id = Column(Integer, ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    account = relationship('Account', back_populates='auths')
    socials = relationship('SocialIntegration',
                           back_populates='auth_data',
                           cascade='all, delete',
                           passive_deletes=True)

    @hybrid_property
    def is_confirmed(self):
        return bool(self.confirmed_at)

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
