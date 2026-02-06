"""XBRL tag-to-canonical-name mappings per financial statement.

Each metric maps to a priority-ordered list of XBRL tags.
Companies use different tags for the same concept; we try each in order
and use the first one that has data.
"""

from __future__ import annotations

# statement name → { canonical_name → [ordered XBRL tags] }

INCOME_STATEMENT: dict[str, list[str]] = {
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "SalesRevenueServicesNet",
    ],
    "cost_of_revenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
        "CostOfGoodsSold",
        "CostOfGoodsAndServiceExcludingDepreciationDepletionAndAmortization",
    ],
    "gross_profit": [
        "GrossProfit",
    ],
    "operating_expenses": [
        "OperatingExpenses",
        "CostsAndExpenses",
    ],
    "research_and_development": [
        "ResearchAndDevelopmentExpense",
        "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
    ],
    "selling_general_admin": [
        "SellingGeneralAndAdministrativeExpense",
        "SellingAndMarketingExpense",
        "GeneralAndAdministrativeExpense",
    ],
    "operating_income": [
        "OperatingIncomeLoss",
    ],
    "interest_expense": [
        "InterestExpense",
        "InterestExpenseDebt",
        "InterestIncomeExpenseNet",
    ],
    "income_before_tax": [
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        "IncomeLossFromContinuingOperationsBeforeIncomeTaxesDomestic",
    ],
    "income_tax": [
        "IncomeTaxExpenseBenefit",
    ],
    "net_income": [
        "NetIncomeLoss",
        "ProfitLoss",
        "NetIncomeLossAvailableToCommonStockholdersBasic",
    ],
    "eps_basic": [
        "EarningsPerShareBasic",
    ],
    "eps_diluted": [
        "EarningsPerShareDiluted",
    ],
    "shares_basic": [
        "WeightedAverageNumberOfShareOutstandingBasicAndDiluted",
        "WeightedAverageNumberOfSharesOutstandingBasic",
        "CommonStockSharesOutstanding",
    ],
    "shares_diluted": [
        "WeightedAverageNumberOfDilutedSharesOutstanding",
    ],
}

BALANCE_SHEET: dict[str, list[str]] = {
    "total_assets": [
        "Assets",
    ],
    "current_assets": [
        "AssetsCurrent",
    ],
    "cash_and_equivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsAndShortTermInvestments",
        "Cash",
    ],
    "short_term_investments": [
        "ShortTermInvestments",
        "AvailableForSaleSecuritiesCurrent",
        "MarketableSecuritiesCurrent",
    ],
    "accounts_receivable": [
        "AccountsReceivableNetCurrent",
        "AccountsReceivableNet",
        "ReceivablesNetCurrent",
    ],
    "inventory": [
        "InventoryNet",
        "InventoryFinishedGoods",
    ],
    "total_liabilities": [
        "Liabilities",
        "LiabilitiesAndStockholdersEquity",
    ],
    "current_liabilities": [
        "LiabilitiesCurrent",
    ],
    "accounts_payable": [
        "AccountsPayableCurrent",
        "AccountsPayableAndAccruedLiabilitiesCurrent",
    ],
    "long_term_debt": [
        "LongTermDebt",
        "LongTermDebtNoncurrent",
        "LongTermDebtAndCapitalLeaseObligations",
    ],
    "short_term_debt": [
        "ShortTermBorrowings",
        "DebtCurrent",
        "CommercialPaper",
    ],
    "total_debt": [
        "LongTermDebtAndCapitalLeaseObligationsIncludingCurrentMaturities",
        "DebtAndCapitalLeaseObligations",
    ],
    "stockholders_equity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "retained_earnings": [
        "RetainedEarningsAccumulatedDeficit",
    ],
    "common_stock_shares": [
        "CommonStockSharesOutstanding",
        "CommonStockSharesIssued",
    ],
}

CASH_FLOW: dict[str, list[str]] = {
    "operating_cash_flow": [
        "NetCashProvidedByUsedInOperatingActivities",
        "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
    ],
    "depreciation_amortization": [
        "DepreciationDepletionAndAmortization",
        "DepreciationAndAmortization",
        "Depreciation",
    ],
    "capital_expenditure": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsForCapitalImprovements",
    ],
    "investing_cash_flow": [
        "NetCashProvidedByUsedInInvestingActivities",
        "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations",
    ],
    "financing_cash_flow": [
        "NetCashProvidedByUsedInFinancingActivities",
        "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations",
    ],
    "dividends_paid": [
        "PaymentsOfDividendsCommonStock",
        "PaymentsOfDividends",
        "PaymentsOfOrdinaryDividends",
    ],
    "share_repurchase": [
        "PaymentsForRepurchaseOfCommonStock",
        "PaymentsForRepurchaseOfEquity",
    ],
    "stock_based_compensation": [
        "ShareBasedCompensation",
        "AllocatedShareBasedCompensationExpense",
    ],
    "dividends_per_share": [
        "CommonStockDividendsPerShareDeclared",
        "CommonStockDividendsPerShareCashPaid",
    ],
}

# Lookup: statement name → tag mappings
STATEMENT_TAGS: dict[str, dict[str, list[str]]] = {
    "income": INCOME_STATEMENT,
    "balance": BALANCE_SHEET,
    "cashflow": CASH_FLOW,
}

# Reverse lookup: XBRL tag → (canonical_name, statement)
TAG_LOOKUP: dict[str, tuple[str, str]] = {}
for _stmt_name, _metrics in STATEMENT_TAGS.items():
    for _canonical, _tags in _metrics.items():
        for _tag in _tags:
            if _tag not in TAG_LOOKUP:
                TAG_LOOKUP[_tag] = (_canonical, _stmt_name)

# All canonical names per statement
STATEMENT_COLUMNS: dict[str, list[str]] = {
    stmt: list(metrics.keys()) for stmt, metrics in STATEMENT_TAGS.items()
}
