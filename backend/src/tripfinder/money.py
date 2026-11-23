"""Money and price ranges. Arithmetic across currencies is refused, never converted silently."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


class CurrencyMismatch(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    @classmethod
    def of(cls, amount: float | str | Decimal, currency: str = "CAD") -> Money:
        return cls(Decimal(str(amount)), currency.upper())

    def _check(self, other: Money) -> None:
        if not isinstance(other, Money):
            raise TypeError(f"expected Money, got {type(other).__name__}")
        if other.currency != self.currency:
            raise CurrencyMismatch(f"{self.currency} vs {other.currency}")

    def __add__(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        self._check(other)
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: float | Decimal) -> Money:
        if isinstance(factor, Money):
            raise TypeError("cannot multiply Money by Money")
        return Money(self.amount * Decimal(str(factor)), self.currency)

    __rmul__ = __mul__

    def __lt__(self, other: Money) -> bool:
        self._check(other)
        return self.amount < other.amount

    def __le__(self, other: Money) -> bool:
        self._check(other)
        return self.amount <= other.amount

    def rounded(self) -> Money:
        return Money(self.amount.quantize(Decimal(1), rounding=ROUND_HALF_UP), self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.rounded().amount:,}"


@dataclass(frozen=True, slots=True)
class PriceRange:
    low: Money
    expected: Money
    high: Money

    def __post_init__(self) -> None:
        self.low._check(self.expected)
        self.low._check(self.high)
        if not (self.low <= self.expected <= self.high):
            raise ValueError(f"range out of order: {self.low} / {self.expected} / {self.high}")

    @property
    def currency(self) -> str:
        return self.low.currency

    def __add__(self, other: PriceRange) -> PriceRange:
        return PriceRange(self.low + other.low, self.expected + other.expected, self.high + other.high)

    def __mul__(self, factor: float | Decimal) -> PriceRange:
        return PriceRange(self.low * factor, self.expected * factor, self.high * factor)

    __rmul__ = __mul__

    @classmethod
    def zero(cls, currency: str = "CAD") -> PriceRange:
        z = Money.of(0, currency)
        return cls(z, z, z)

    def as_dict(self) -> dict[str, float]:
        return {
            "low": float(self.low.rounded().amount),
            "expected": float(self.expected.rounded().amount),
            "high": float(self.high.rounded().amount),
        }
