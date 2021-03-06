import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, registry
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.dialects.postgresql import UUID


mapper_registry = registry()


class Base(metaclass=DeclarativeMeta):
    __abstract__ = True
    # these are supplied by the sqlalchemy2-stubs, so may be omitted
    # when they are installed
    registry = mapper_registry
    metadata = mapper_registry.metadata
    __init__ = mapper_registry.constructor

    def __repr__(self):
        class_ = self.__class__.__name__
        # @INFO: self doesn't have __mapper__ member BUT all base's children do!
        # pylint: disable=no-member
        attrs = sorted((k, getattr(self, k)) for k in self.__mapper__.columns.keys())
        # pylint: enable=no-member
        sattrs = ", ".join("{}={!r}".format(*x) for x in attrs)
        return f"{class_}({ sattrs})"


class Action_Type(Base):
    __tablename__ = "action_type"
    name = Column(String, primary_key=True)
    actions_rel: Mapped[str] = relationship("Actions", back_populates="action_type_rel")


class Wallets(Base):
    __tablename__ = "wallets"
    name = Column(String, primary_key=True)
    actions_rel: Mapped[str] = relationship("Actions", back_populates="wallet_rel")


class Coins(Base):
    __tablename__ = "coins"
    coin_token = Column(String, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    actions_rel: Mapped[str] = relationship("Actions", back_populates="coin_rel")


class Actions(Base):
    __tablename__ = "actions"
    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True)
    utc_date = Column(DateTime(timezone=False))
    action_type: str = Column(String, ForeignKey("action_type.name"))
    coin: str = Column(String, ForeignKey("coins.coin_token"))
    action_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), nullable=False)
    amount: float = Column(Float(precision=13), nullable=False)
    investment: float = Column(Float(precision=7), nullable=False)
    wallet: str = Column(String, ForeignKey("wallets.name"))
    wallet_rel: Mapped[str] = relationship("Wallets", back_populates="actions_rel")
    coin_rel: Mapped[str] = relationship("Coins", back_populates="actions_rel")
    action_type_rel: Mapped[str] = relationship("Action_Type", back_populates="actions_rel")


class Portfolio(Base):
    __tablename__ = "portfolio"
    coin: str = Column(String, primary_key=True)
    amount: float = Column(Float(precision=13), nullable=False)
    investment: float = Column(Float(precision=7), nullable=False)
    min_price: float = Column(Float(precision=7), nullable=False)


class Actual_Investment(Base):
    __tablename__ = "actual_investment"
    investment: float = Column(Float(precision=7), primary_key=True)
