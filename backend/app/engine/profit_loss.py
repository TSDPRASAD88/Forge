"""Profit and loss generators. Same structure as the percentage and ratio generators."""

import random
from fractions import Fraction
from typing import Callable

from app.domain.enums import Difficulty
from app.domain.models import SolutionStep
from app.engine.generator import CLEAN_BASES, Draft, _show, _unit


def _profit_percent(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.HARD:
        cp = rng.choice(CLEAN_BASES)
        sp = rng.randint(cp + 1, cp * 2)
        answer = Fraction((sp - cp) * 100, cp)
    else:
        a = rng.choice([10, 20, 25, 50]) if d == Difficulty.EASY else rng.randrange(5, 96, 5)
        cp = _unit(a) * rng.randint(2, 20)
        sp = cp + a * cp // 100
        answer = Fraction(a)             # chosen first; the solver re-derives it from cp and sp
    profit = sp - cp
    return Draft(
        params={"cp": cp, "sp": sp},
        text=f"An article is bought for Rs {cp} and sold for Rs {sp}. What is the profit percent?",
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="Find the profit.", expression=f"{sp} − {cp} = {profit}"),
            SolutionStep(description="Divide the profit by the COST price and multiply by 100.",
                         expression=f"({profit}/{cp}) × 100", result=_show(answer)),
        ],
        traps=[
            (Fraction(profit * 100, sp), "You divided the profit by the SELLING price. Profit percent is always measured on the COST price."),
            (Fraction(profit), "You gave the profit in rupees. Convert it into a percentage of the cost price."),
            (Fraction(sp * 100, cp), "You gave the selling price as a percent of the cost price. Subtract 100 to get the profit percent."),
        ],
    )


def _loss_percent(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.HARD:
        cp = rng.choice(CLEAN_BASES)
        sp = rng.randint(max(1, cp // 4), cp - 1)
        answer = Fraction((cp - sp) * 100, cp)
    else:
        a = rng.choice([10, 20, 25, 50]) if d == Difficulty.EASY else rng.randrange(5, 91, 5)
        cp = _unit(a) * rng.randint(2, 20)
        sp = cp - a * cp // 100
        answer = Fraction(a)
    loss = cp - sp
    return Draft(
        params={"cp": cp, "sp": sp},
        text=f"An article is bought for Rs {cp} and sold for Rs {sp}. What is the loss percent?",
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="Find the loss.", expression=f"{cp} − {sp} = {loss}"),
            SolutionStep(description="Divide the loss by the COST price and multiply by 100.",
                         expression=f"({loss}/{cp}) × 100", result=_show(answer)),
        ],
        traps=[
            (Fraction(loss * 100, sp), "You divided the loss by the SELLING price. Loss percent is always measured on the COST price."),
            (Fraction(loss), "You gave the loss in rupees. Convert it into a percentage of the cost price."),
            (Fraction(sp * 100, cp), "You gave the selling price as a percent of the cost price. Subtract it from 100 to get the loss percent."),
        ],
    )


def _selling_price(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        p = rng.choice([10, 20, 25, 50])
        cp = rng.randrange(100, 2001, 100)
    elif d == Difficulty.MEDIUM:
        p = rng.randrange(5, 46, 5)
        cp = rng.randrange(200, 5001, 20)
    else:
        p = rng.randint(1, 60)
        cp = rng.randrange(250, 9001, 20)
    profit = Fraction(cp * p, 100)
    answer = cp + profit
    return Draft(
        params={"cp": cp, "p": p},
        text=f"An article is bought for Rs {cp} and sold at a profit of {p}%. What is the selling price?",
        unit="Rs",
        answer=answer,
        steps=[
            SolutionStep(description="Find the profit amount as a percentage of the cost price.",
                         expression=f"{cp} × {p}/100 = {_show(profit)}"),
            SolutionStep(description="Add the profit to the cost price.",
                         expression=f"{cp} + {_show(profit)}", result=_show(answer)),
        ],
        traps=[
            (profit, "You stopped at the profit amount. The selling price is the cost price plus the profit."),
            (cp - profit, "You subtracted the profit instead of adding it."),
            (Fraction(cp + p), f"You added {p} rupees. The profit is {p}% of the cost price, not {p} rupees."),
        ],
    )


def _cost_price(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        loss = rng.choice([10, 20, 25, 50])
        n = rng.randint(2, 20)
    elif d == Difficulty.MEDIUM:
        loss = rng.randint(2, 60)
        n = rng.randint(1, 10)
    else:
        loss = rng.randint(2, 90)
        n = rng.randint(1, 10)
    cp = _unit(loss) * n
    sp = cp - loss * cp // 100
    answer = Fraction(cp)                 # chosen first; the solver re-derives it from sp and the loss
    remaining = 100 - loss
    return Draft(
        params={"sp": sp, "l": loss},
        text=f"An article is sold for Rs {sp} at a loss of {loss}%. What is the cost price?",
        unit="Rs",
        answer=answer,
        steps=[
            SolutionStep(description=f"With a {loss}% loss, the selling price is {remaining}% of the cost price.",
                         expression=f"({remaining}/100) × CP = {sp}"),
            SolutionStep(description="Solve for the cost price.",
                         expression=f"CP = {sp} × 100 / {remaining}", result=_show(answer)),
        ],
        traps=[
            (Fraction(sp * (100 + loss), 100), f"You added {loss}% of the selling price. The loss is {loss}% of the COST price, so divide by (100 − {loss})%."),
            (Fraction(sp * loss, 100), f"You found {loss}% of the selling price only."),
            (Fraction(sp * 100, 100 + loss), "You treated it as a profit. A loss means the selling price is below the cost price, so divide by (100 − loss)%."),
        ],
    )


def _markup_discount(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        m, dsc = rng.choice([10, 20, 25, 50]), rng.choice([10, 20, 25])
    elif d == Difficulty.MEDIUM:
        m, dsc = rng.randrange(5, 51, 5), rng.randrange(5, 31, 5)
    else:
        m, dsc = rng.randint(5, 80), rng.randint(2, 50)
    # shortcut formula m - d - md/100 (the solver uses multipliers instead)
    answer = Fraction(m - dsc) - Fraction(m * dsc, 100)
    mp = 100 + m
    sp = Fraction(mp * (100 - dsc), 100)
    return Draft(
        params={"m": m, "d": dsc},
        text=(f"A shopkeeper marks his goods {m}% above the cost price and then allows a discount of {dsc}%. "
              f"What is his net gain or loss percent? (Use a negative value for a loss.)"),
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="Assume the cost price is Rs 100 and add the markup to get the marked price.",
                         expression=f"100 + {m} = {mp}"),
            SolutionStep(description="Apply the discount to the MARKED price to get the selling price.",
                         expression=f"{mp} × {100 - dsc}/100 = {_show(sp)}"),
            SolutionStep(description="Compare the selling price with the cost price of 100.",
                         expression=f"{_show(sp)} − 100", result=_show(answer)),
        ],
        traps=[
            (Fraction(m - dsc), "You subtracted the percentages directly. The discount applies to the MARKED price, not the cost price."),
            (-answer, "The sign is flipped. Check whether the selling price ends up above or below the cost price."),
            (Fraction(m - dsc) + Fraction(m * dsc, 100),
             "You added the (markup × discount)/100 term. It must be subtracted, because the discount is taken off the larger marked price."),
            (Fraction(m), "You ignored the discount and gave only the markup."),
        ],
        allow_negative=True,
    )


def _two_articles(rng: random.Random, d: Difficulty) -> Draft:
    if d == Difficulty.EASY:
        p = rng.choice([10, 20, 30])
    elif d == Difficulty.MEDIUM:
        p = rng.randrange(5, 41, 5)
    else:
        p = rng.randint(2, 45)
    answer = Fraction(p * p, 100)         # shortcut result (the solver derives it from cost prices)
    return Draft(
        params={"p": p},
        text=(f"Two articles are sold at the same price, one at a gain of {p}% and the other at a loss of {p}%. "
              f"What is the overall loss percent?"),
        unit="%",
        answer=answer,
        steps=[
            SolutionStep(description="When two articles are sold at the same price with an equal gain and loss percent, there is always a net loss of (percent²)/100 percent.",
                         expression=f"loss % = {p}² / 100"),
            SolutionStep(description="Substitute the value.",
                         expression=f"{p * p} / 100", result=_show(answer)),
        ],
        traps=[
            (Fraction(0), "You assumed an equal gain and loss cancel out. They apply to different cost prices, so there is a net loss."),
            (Fraction(p), f"You gave {p}% as the loss. The gain and loss are on different cost prices, so the net loss is {p}²/100 percent."),
            (Fraction(p * p), "You forgot to divide by 100."),
            (Fraction(p * p, 10), "You divided by 10 instead of 100."),
        ],
    )


PL_GENERATORS: dict[str, Callable[[random.Random, Difficulty], Draft]] = {
    "pl_profit_percent": _profit_percent,
    "pl_loss_percent": _loss_percent,
    "pl_selling_price": _selling_price,
    "pl_cost_price": _cost_price,
    "pl_markup_discount": _markup_discount,
    "pl_two_articles": _two_articles,
}