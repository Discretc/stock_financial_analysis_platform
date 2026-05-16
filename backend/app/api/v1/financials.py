"""
Financials API endpoints — income statement, balance sheet, cash flow.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ExternalAPIError
from app.schemas.financials import (
    BalanceSheetResponse,
    CashFlowStatementResponse,
    IncomeStatementResponse,
)
from app.services.financial_service import FinancialService
from app.services.fmp_service import fmp_client

router = APIRouter(prefix="/financials", tags=["Financial Statements"])

PeriodType = Literal["annual", "quarterly"]


@router.get(
    "/{ticker}/income-statement",
    response_model=IncomeStatementResponse,
    summary="Income statement with common-size percentages and YoY growth",
)
async def get_income_statement(
    ticker: str,
    period: PeriodType = Query(default="annual"),
    limit: int = Query(default=10, ge=1, le=40),
    db: AsyncSession = Depends(get_db),
):
    service = FinancialService(db)
    try:
        records = await service.get_income_statements(ticker, period=period, limit=limit)
        if not records:
            await service.fetch_and_store_income_statements(ticker, period=period, limit=limit)
            await db.commit()
            records = await service.get_income_statements(ticker, period=period, limit=limit)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data for {ticker}")

    return IncomeStatementResponse(ticker=ticker.upper(), period=period, statements=records)


@router.get(
    "/{ticker}/balance-sheet",
    response_model=BalanceSheetResponse,
    summary="Balance sheet with common-size percentages",
)
async def get_balance_sheet(
    ticker: str,
    period: PeriodType = Query(default="annual"),
    limit: int = Query(default=10, ge=1, le=40),
    db: AsyncSession = Depends(get_db),
):
    service = FinancialService(db)
    try:
        records = await service.get_balance_sheets(ticker, period=period, limit=limit)
        if not records:
            await service.fetch_and_store_balance_sheets(ticker, period=period, limit=limit)
            await db.commit()
            records = await service.get_balance_sheets(ticker, period=period, limit=limit)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data for {ticker}")

    return BalanceSheetResponse(ticker=ticker.upper(), period=period, statements=records)


@router.get(
    "/{ticker}/cash-flow",
    response_model=CashFlowStatementResponse,
    summary="Cash flow statement with common-size percentages",
)
async def get_cash_flow(
    ticker: str,
    period: PeriodType = Query(default="annual"),
    limit: int = Query(default=10, ge=1, le=40),
    db: AsyncSession = Depends(get_db),
):
    service = FinancialService(db)
    try:
        records = await service.get_cash_flow_statements(ticker, period=period, limit=limit)
        if not records:
            await service.fetch_and_store_cash_flows(ticker, period=period, limit=limit)
            await db.commit()
            records = await service.get_cash_flow_statements(ticker, period=period, limit=limit)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if not records:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No data for {ticker}")

    return CashFlowStatementResponse(ticker=ticker.upper(), period=period, statements=records)


@router.get(
    "/{ticker}/ratios",
    summary="Financial ratios (margins, ROE, PE, etc.)",
)
async def get_ratios(
    ticker: str,
    period: PeriodType = Query(default="annual"),
    limit: int = Query(default=10, ge=1, le=40),
):
    try:
        raw = await fmp_client.get_ratios(ticker, period=period)
    except ExternalAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))
    return {"ticker": ticker.upper(), "period": period, "data": raw[:limit]}
