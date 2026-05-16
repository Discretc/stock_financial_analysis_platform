"""
Watchlists and Portfolios API endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_verified_user
from app.core.database import get_db
from app.models.user import User
from app.models.watchlist import Portfolio, PortfolioHolding, Watchlist, WatchlistItem
from app.schemas.watchlist import (
    PortfolioCreate,
    PortfolioHoldingCreate,
    PortfolioSchema,
    WatchlistCreate,
    WatchlistItemCreate,
    WatchlistSchema,
)

router = APIRouter(tags=["Watchlists & Portfolios"])


# ---------------------------------------------------------------------------
# Watchlists
# ---------------------------------------------------------------------------

@router.get("/watchlists", response_model=list[WatchlistSchema])
async def list_watchlists(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == current_user.id)
        .options(selectinload(Watchlist.items))
        .order_by(Watchlist.created_at)
    )
    return list(result.scalars().all())


@router.post("/watchlists", response_model=WatchlistSchema, status_code=status.HTTP_201_CREATED)
async def create_watchlist(
    data: WatchlistCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    watchlist = Watchlist(user_id=current_user.id, name=data.name, description=data.description)
    db.add(watchlist)
    await db.flush()
    await db.refresh(watchlist)
    return watchlist


@router.post("/watchlists/{watchlist_id}/items", response_model=WatchlistSchema, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    watchlist_id: uuid.UUID,
    data: WatchlistItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
        .options(selectinload(Watchlist.items))
    )
    watchlist = result.scalar_one_or_none()
    if not watchlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")

    item = WatchlistItem(
        watchlist_id=watchlist_id,
        ticker=data.ticker.upper(),
        exchange=data.exchange,
        notes=data.notes,
        alert_price_above=data.alert_price_above,
        alert_price_below=data.alert_price_below,
    )
    db.add(item)
    await db.flush()
    await db.refresh(watchlist)
    return watchlist


@router.delete("/watchlists/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist(
    watchlist_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    result = await db.execute(
        select(Watchlist).where(Watchlist.id == watchlist_id, Watchlist.user_id == current_user.id)
    )
    watchlist = result.scalar_one_or_none()
    if not watchlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Watchlist not found")
    await db.delete(watchlist)


# ---------------------------------------------------------------------------
# Portfolios
# ---------------------------------------------------------------------------

@router.get("/portfolios", response_model=list[PortfolioSchema])
async def list_portfolios(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.user_id == current_user.id)
        .options(selectinload(Portfolio.holdings))
        .order_by(Portfolio.created_at)
    )
    return list(result.scalars().all())


@router.post("/portfolios", response_model=PortfolioSchema, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    data: PortfolioCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    portfolio = Portfolio(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        currency=data.currency,
    )
    db.add(portfolio)
    await db.flush()
    await db.refresh(portfolio)
    return portfolio


@router.post("/portfolios/{portfolio_id}/holdings", response_model=PortfolioSchema, status_code=status.HTTP_201_CREATED)
async def add_holding(
    portfolio_id: uuid.UUID,
    data: PortfolioHoldingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    result = await db.execute(
        select(Portfolio)
        .where(Portfolio.id == portfolio_id, Portfolio.user_id == current_user.id)
        .options(selectinload(Portfolio.holdings))
    )
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    holding = PortfolioHolding(
        portfolio_id=portfolio_id,
        ticker=data.ticker.upper(),
        shares=data.shares,
        average_cost=data.average_cost,
        currency=data.currency,
        notes=data.notes,
    )
    db.add(holding)
    await db.flush()
    await db.refresh(portfolio)
    return portfolio
