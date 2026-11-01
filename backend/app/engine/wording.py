"""Alternative wordings for each question type.

Rules for every template:
- the FIRST template of each type is the original wording from the generator (a test checks this);
- use only params that appear in the text, in the same order as TEXT_PARAM_ORDER in the validator;
- no digits other than placeholders, and keep what is being asked identical, because the solution
  steps and wrong-option notes depend on it.
"""

import random

WORDINGS: dict[str, list[str]] = {
    # ---- percentages ----
    "percent_of_number": [
        "What is {percent}% of {base}?",
        "Find {percent}% of {base}.",
        "Calculate {percent}% of {base}.",
    ],
    "what_percent": [
        "{x} is what percent of {y}?",
        "Express {x} as a percentage of {y}.",
        "{x} out of {y} is what percent?",
    ],
    "percent_change": [
        "The value of an item changes from {old} to {new}. What is the percentage {direction}?",
        "The price of a product moves from {old} to {new}. By what percent does it {direction}?",
        "A quantity goes from {old} to {new}. Find the percentage {direction}.",
    ],
    "successive_change": [
        "A price is {dir1}d by {p1}% and then {dir2}d by {p2}%. What is the net percentage change? "
        "(Use a negative value for a net decrease.)",
        "The price of an item is {dir1}d by {p1}% and then {dir2}d by {p2}%. What is the overall percentage change? "
        "(Use a negative value for a net decrease.)",
        "A population is {dir1}d by {p1}% in one year and {dir2}d by {p2}% in the next. "
        "What is the net percentage change over the two years? (Use a negative value for a net decrease.)",
    ],
    "find_original": [
        "{x} is {p}% of what number?",
        "{x} is {p}% of a certain number. Find the number.",
        "{x} represents {p}% of a number. What is that number?",
    ],
    "discount_price": [
        "An article is marked at Rs {price}. A discount of {discount}% is given on it. What is the selling price?",
        "A shirt has a marked price of Rs {price}. The shop offers {discount}% off. What is the selling price?",
        "The list price of a gadget is Rs {price}. It is sold at a discount of {discount}%. "
        "What price does the customer pay?",
    ],
    # ---- ratios ----
    "ratio_share": [
        "A sum of Rs {total} is divided between two people in the ratio {a}:{b}. How much does the first person get?",
        "Rs {total} is shared between two friends in the ratio {a}:{b}. How much does the first friend get?",
        "A prize of Rs {total} is split between two winners in the ratio {a}:{b}. What is the first winner's share?",
    ],
    "ratio_missing_term": [
        "The ratio of two numbers is {a}:{b}. If the first number is {x}, what is the second number?",
        "Two numbers are in the ratio {a}:{b}. The first number is {x}. Find the second number.",
        "In a mixture the quantities of two ingredients are in the ratio {a}:{b}. "
        "If the first ingredient is {x} units, how many units of the second are there?",
    ],
    "proportion": [
        "If {a} {item} cost Rs {b}, what is the cost of {c} {item}?",
        "{a} {item} are bought for Rs {b}. At the same rate, how much will {c} {item} cost?",
        "The price of {a} {item} is Rs {b}. What is the price of {c} {item} at the same rate?",
    ],
    "ratio_difference": [
        "Two numbers are in the ratio {a}:{b} and their difference is {d}. What is the larger number?",
        "The ratio of two numbers is {a}:{b} and they differ by {d}. Find the larger number.",
        "Two quantities are in the ratio {a}:{b}. If the difference between them is {d}, "
        "what is the larger quantity?",
    ],
    "ratio_chain": [
        "The ratio A:B is {p}:{q} and the ratio B:C is {r}:{s}. If C is {x}, what is A?",
        "A, B and C are related by A:B = {p}:{q} and B:C = {r}:{s}. If C is {x}, find A.",
    ],
    # ---- profit and loss ----
    "pl_profit_percent": [
        "An article is bought for Rs {cp} and sold for Rs {sp}. What is the profit percent?",
        "A trader buys an item for Rs {cp} and sells it for Rs {sp}. What is his profit percent?",
        "Goods costing Rs {cp} are sold for Rs {sp}. Find the profit percent.",
    ],
    "pl_loss_percent": [
        "An article is bought for Rs {cp} and sold for Rs {sp}. What is the loss percent?",
        "A trader buys an item for Rs {cp} and sells it for Rs {sp}. What is his loss percent?",
        "Goods costing Rs {cp} are sold for Rs {sp}. Find the loss percent.",
    ],
    "pl_selling_price": [
        "An article is bought for Rs {cp} and sold at a profit of {p}%. What is the selling price?",
        "A trader buys an item for Rs {cp} and wants a profit of {p}%. At what price should he sell it?",
        "An item costing Rs {cp} is sold at a gain of {p}%. What is its selling price?",
    ],
    "pl_cost_price": [
        "An article is sold for Rs {sp} at a loss of {l}%. What is the cost price?",
        "A trader sells an item for Rs {sp} and makes a loss of {l}%. What did the item cost him?",
        "An item sold for Rs {sp} brings a loss of {l}%. Find its cost price.",
    ],
    "pl_markup_discount": [
        "A shopkeeper marks his goods {m}% above the cost price and then allows a discount of {d}%. "
        "What is his net gain or loss percent? (Use a negative value for a loss.)",
        "A trader increases the cost price of his goods by {m}% to get the marked price, and then gives "
        "a discount of {d}% on the marked price. What is his net gain or loss percent? "
        "(Use a negative value for a loss.)",
    ],
    "pl_two_articles": [
        "Two articles are sold at the same price, one at a gain of {p}% and the other at a loss of {p}%. "
        "What is the overall loss percent?",
        "A dealer sells two articles at the same price. On one he gains {p}% and on the other he loses {p}%. "
        "What is his overall loss percent?",
    ],
    # ---- time and work ----
    "tw_together": [
        "A can complete a piece of work in {x} days and B can complete it in {y} days. "
        "In how many days will they finish it working together?",
        "Worker A needs {x} days to finish a job and worker B needs {y} days. "
        "How many days will they take to finish it together?",
        "A alone can do a job in {x} days and B alone can do it in {y} days. "
        "Working together, how long will they take to complete the job?",
    ],
    "tw_alone": [
        "A and B together can finish a piece of work in {t} days. A alone can finish it in {x} days. "
        "In how many days can B alone finish it?",
        "Working together, A and B finish a job in {t} days. A alone would take {x} days. "
        "How many days would B alone take?",
        "A and B can complete a task together in {t} days. If A alone can complete it in {x} days, "
        "in how many days can B alone complete it?",
    ],
    "tw_leaving": [
        "A can finish a piece of work in {x} days and B in {y} days. They start working together, "
        "but A leaves after {d} days. In how many more days will B finish the remaining work?",
        "A takes {x} days and B takes {y} days to finish a job alone. They begin together, "
        "but A quits after {d} days. How many more days does B need to finish the job?",
    ],
    "tw_wages": [
        "A can do a piece of work in {x} days and B in {y} days. They work together and are paid "
        "Rs {w} in total. How much does A receive?",
        "A can finish a job in {x} days and B in {y} days. Working together they earn Rs {w}. "
        "How much of it does A get?",
    ],
    "tw_pipes": [
        "A pipe can fill an empty tank in {f} hours, and a drain can empty the full tank in {e} hours. "
        "If both are opened together, in how many hours will the empty tank be filled?",
        "An inlet pipe fills an empty tank in {f} hours and an outlet pipe empties the full tank in {e} hours. "
        "If both are opened together, how many hours does it take to fill the empty tank?",
    ],
    # ---- averages and mixtures ----
    "avg_new_member": [
        "The average of {n} numbers is {a}. When a new number is added, the average becomes {b}. "
        "What is the new number?",
        "The mean of {n} numbers is {a}. After one more number is included, the mean becomes {b}. "
        "What is the number that was included?",
        "The average age of {n} people is {a} years. When one more person joins, the average age becomes "
        "{b} years. What is the age of the new person?",
    ],
    "avg_replace": [
        "The average of {n} numbers is {a}. If one of the numbers, {p}, is replaced by {q}, "
        "what is the new average?",
        "The mean of {n} numbers is {a}. If the number {p} is replaced by {q}, what is the new mean?",
        "The average of {n} numbers is {a}. One number, {p}, is removed and {q} is put in its place. "
        "Find the new average.",
    ],
    "avg_combined": [
        "One class of {n1} students has an average score of {m1}, and another class of {n2} students "
        "has an average score of {m2}. What is the average score of all the students together?",
        "A group of {n1} students scored an average of {m1}, and a second group of {n2} students scored "
        "an average of {m2}. What is the average score of the two groups combined?",
    ],
    "avg_speed": [
        "A vehicle travels from city A to city B at {x} km/h and returns along the same route at "
        "{y} km/h. What is its average speed for the whole round trip?",
        "A car goes from P to Q at {x} km/h and comes back along the same road at {y} km/h. "
        "What is its average speed for the whole journey?",
    ],
    "mix_quantity": [
        "How many kg of sugar costing Rs {y} per kg must be mixed with {q} kg of sugar costing "
        "Rs {x} per kg to get a mixture worth Rs {z} per kg?",
        "Sugar at Rs {y} per kg is mixed with {q} kg of sugar at Rs {x} per kg to make a mixture worth "
        "Rs {z} per kg. How many kg of the dearer sugar are used?",
    ],
    "mix_replace": [
        "A vessel contains {v} litres of pure milk. {a} litres are removed and replaced with water. "
        "The same operation is then repeated once more. How many litres of milk are now in the vessel?",
        "A container holds {v} litres of pure milk. {a} litres are drawn off and replaced by water, "
        "and then the same is done once again. How many litres of milk remain?",
    ],
    # ---- interest ----
    "int_si": [
        "What is the simple interest on Rs {p} for {t} years at {r}% per annum?",
        "A sum of Rs {p} is lent for {t} years at {r}% per annum simple interest. How much interest is earned?",
        "Find the simple interest earned on Rs {p} in {t} years at {r}% per annum.",
    ],
    "int_si_rate": [
        "A sum of Rs {p} earns a simple interest of Rs {si} in {t} years. What is the rate of interest per annum?",
        "Rs {p} earns simple interest of Rs {si} in {t} years. At what rate per annum was it lent?",
        "A person lends Rs {p} and receives Rs {si} as simple interest after {t} years. "
        "Find the annual rate of interest.",
    ],
    "int_si_time": [
        "A sum of Rs {p} earns a simple interest of Rs {si} at {r}% per annum. For how many years was it invested?",
        "Rs {p} earns simple interest of Rs {si} at {r}% per annum. How many years did it take?",
        "A sum of Rs {p} fetches Rs {si} as simple interest at {r}% per annum. For what period was it invested?",
    ],
    "int_ci_amount": [
        "What is the amount on Rs {p} for {n} years at {r}% per annum, compounded annually?",
        "Rs {p} is invested for {n} years at {r}% per annum, compounded annually. What is the amount at the end?",
        "A deposit of Rs {p} grows for {n} years at {r}% per annum compounded annually. "
        "What is the maturity amount?",
    ],
    "int_ci_diff": [
        "What is the difference between the compound interest and the simple interest on Rs {p} "
        "for {n} years at {r}% per annum, compounded annually?",
        "Find the difference between the compound interest and the simple interest on Rs {p} "
        "for {n} years at {r}% per annum, compounded annually.",
        "On a sum of Rs {p} for {n} years at {r}% per annum, how much more is the compound interest "
        "(compounded annually) than the simple interest?",
    ],
    "int_si_multiple": [
        "In how many years will a sum of money become {k} times itself at {r}% per annum simple interest?",
        "A sum of money becomes {k} times itself in some years at {r}% per annum simple interest. "
        "How many years does this take?",
        "How long will it take for money to become {k} times itself at {r}% per annum simple interest?",
    ],
}


def pick_wording(rng: random.Random, subtype: str, original: str, params: dict) -> str:
    templates = WORDINGS.get(subtype)
    if not templates:
        return original
    return rng.choice(templates).format(**params)