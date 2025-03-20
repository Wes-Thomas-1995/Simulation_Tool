# API_CONNECTIONS/views.py
import re
import os
import json
import urllib.parse
import pandas as pd
import yfinance as yf
from datetime import datetime
from urllib.parse import unquote
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from dateutil.relativedelta import relativedelta
from django.views.decorators.csrf import csrf_exempt







@api_view(['GET'])
def simulation_view(
    request,
    INVESTMENT_TYPE,
    INITIAL_INVESTMENT_AMOUNT,
    PERIODIC_INVESTMENT_AMOUNT,
    PERIODIC_OPTIONS,
    HISTORY,
    HISTORY_OPTIONS,
    INTEREST_RATE,
    COMPOUND_FREQUENCY,
    EQUITIES,
    REOCCURING_AMOUNT,
    REOCCURING_FREQUENCY,
    INDEPEDENT_INVESTMENTS
):
    try:
        # Handle "NA" and blank values
        INTEREST_RATE = float(INTEREST_RATE) if INTEREST_RATE != "NA" else 0.0
        HISTORY_OPTIONS = HISTORY_OPTIONS if HISTORY_OPTIONS != "NA" else None
        PERIODIC_OPTIONS = PERIODIC_OPTIONS if PERIODIC_OPTIONS != "NA" else None
        REOCCURING_FREQUENCY = REOCCURING_FREQUENCY if REOCCURING_FREQUENCY != "NA" else None
        COMPOUND_FREQUENCY = COMPOUND_FREQUENCY if COMPOUND_FREQUENCY != "NA" else None
        EQUITIES = EQUITIES if EQUITIES not in [None, ""] else "NA"
        INDEPEDENT_INVESTMENTS = INDEPEDENT_INVESTMENTS if INDEPEDENT_INVESTMENTS not in [None, ""] else "NA"

        WATCHLIST, WEIGHTS = [], []
        INDEPENDENT_VALUES, INDEPENDENT_DATES = [], []

        # Parse equities
        if INVESTMENT_TYPE == "Equities" and EQUITIES != "NA":
            EQUITIES_LIST = EQUITIES.split(",")
            WATCHLIST = [eq.split("_")[0] for eq in EQUITIES_LIST]
            WEIGHTS = [float(eq.split("_")[1]) / 100 for eq in EQUITIES_LIST]

        # Parse independent investments
        if INDEPEDENT_INVESTMENTS != "NA":
            independent_list = INDEPEDENT_INVESTMENTS.split(";")
            INDEPENDENT_VALUES = [
                float(item.split(",")[0].split("_")[1]) for item in independent_list
            ]
            INDEPENDENT_DATES = [
                item.split(",")[1].split("_")[1] for item in independent_list
            ]

        # Run the simulation function
        simulation_output = SIMULATION_FUNCTION(
            INVESTMENT_TYPE=INVESTMENT_TYPE,
            WATCHLIST=WATCHLIST,
            WEIGHTS=WEIGHTS,
            INTEREST_RATE=INTEREST_RATE,
            COMPOUND_FREQUENCY=COMPOUND_FREQUENCY,
            HISTORY=int(HISTORY),
            HISTORY_OPTIONS=HISTORY_OPTIONS,
            INITIAL_INVESTMENT_AMOUNT=float(INITIAL_INVESTMENT_AMOUNT),
            PERIODIC_INVESTMENT_AMOUNT=float(PERIODIC_INVESTMENT_AMOUNT),
            PERIODIC_OPTIONS=PERIODIC_OPTIONS,
            REOCCURING_AMOUNT=float(REOCCURING_AMOUNT),
            REOCCURING_FREQUENCY=REOCCURING_FREQUENCY,
            INDEPENDENT_VALUES=INDEPENDENT_VALUES,
            INDEPENDENT_DATES=INDEPENDENT_DATES,
        )

        return Response({"status": "success", "data": simulation_output}, status=200)

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=400)
    



def SIMULATION_FUNCTION(
    INVESTMENT_TYPE, WATCHLIST, WEIGHTS, INTEREST_RATE, COMPOUND_FREQUENCY, 
    HISTORY, HISTORY_OPTIONS, INITIAL_INVESTMENT_AMOUNT, PERIODIC_INVESTMENT_AMOUNT, 
    PERIODIC_OPTIONS, REOCCURING_AMOUNT, REOCCURING_FREQUENCY, 
    INDEPENDENT_VALUES, INDEPENDENT_DATES
):


    END_DATE = datetime.now()
    END_DATE_FMT = END_DATE.strftime('%Y-%m-%d')
    WATCHLIST_DF, EOP_DF, EOP_DF_RECURRING, PORTFOLIO_LIST, TABLE = [], [], [], [], []

    MAPPINGS_HISTORY = { "Months": 1, "Quarters": 3, "Years": 12 }
    MAPPINGS = { 
        "Monthly": {"PERIOD": "M", "FREQUENCY": 12},
        "Quarterly": {"PERIOD": "Q", "FREQUENCY": 4},
        "Annually": {"PERIOD": "Y", "FREQUENCY": 1},
    }

    TOTAL_PERIODS = HISTORY * MAPPINGS_HISTORY.get(HISTORY_OPTIONS, 1)
    START_DATE = END_DATE - relativedelta(months=TOTAL_PERIODS)
    START_DATE_FMT = START_DATE.strftime('%Y-%m-%d')

    INDEPENDENT_DATES = [datetime.strptime(DATE, "%Y-%m-%d") for DATE in INDEPENDENT_DATES]
    PERIODS_PER_YEAR = MAPPINGS.get(COMPOUND_FREQUENCY, {}).get("FREQUENCY", 12)
    PERIODIC_INTERVALS = MAPPINGS.get(PERIODIC_OPTIONS, {}).get("FREQUENCY", 1)
    REOCCURING_INTERVALS = MAPPINGS.get(REOCCURING_FREQUENCY, {}).get("FREQUENCY", 1)
    PERIOD = MAPPINGS.get(PERIODIC_OPTIONS, {}).get("PERIOD", "M")
    REOCCURING_PERIOD = MAPPINGS.get(REOCCURING_FREQUENCY, {}).get("PERIOD", "M")
    DIVIDENT_TAX_RATE = 0.15

    output = {"type": INVESTMENT_TYPE, "all": []}


    if INVESTMENT_TYPE == 'Interest': 
        CASH_INVESTED = INITIAL_INVESTMENT_AMOUNT
        PORTFOLIO_VALUE = INITIAL_INVESTMENT_AMOUNT

        for i in range(TOTAL_PERIODS):
            CURRENT_DATE = START_DATE + relativedelta(months=i)

            # Apply compound interest
            PORTFOLIO_VALUE *= (1 + INTEREST_RATE / (100 * PERIODS_PER_YEAR))

            # Add periodic investments
            if (i + 1) % (12 // PERIODIC_INTERVALS) == 0:  
                PORTFOLIO_VALUE += PERIODIC_INVESTMENT_AMOUNT
                CASH_INVESTED += PERIODIC_INVESTMENT_AMOUNT

            # Add reoccurring investments
            if (i + 1) % (12 // REOCCURING_INTERVALS) == 0:  
                PORTFOLIO_VALUE += REOCCURING_AMOUNT
                CASH_INVESTED += REOCCURING_AMOUNT

            # Add independent investments by matching to the nearest date
            for IND_VALUE, IND_DATE in zip(INDEPENDENT_VALUES, INDEPENDENT_DATES):
                days_diff = abs((CURRENT_DATE - IND_DATE).days)
                if days_diff <= 15:  # Allow a 15-day margin to match closest date
                    PORTFOLIO_VALUE += IND_VALUE
                    CASH_INVESTED += IND_VALUE

            # Record the data
            TABLE.append({
                "DATE": CURRENT_DATE.strftime("%Y-%m-%d"),
                "DIVIDENDS_EARNED": 0,
                "CASH_INVESTED": round(CASH_INVESTED, 2),
                "PORTFOLIO_VALUE": round(PORTFOLIO_VALUE, 2),
            })

        # Ensure the table is sorted by ascending dates
        TABLE = sorted(TABLE, key=lambda x: x["DATE"])
        output["all"] = TABLE
        return output
    
    elif INVESTMENT_TYPE == 'Equities': 
        for a in range(len(WATCHLIST)):
            STOCK = yf.Ticker(WATCHLIST[a])
            DATA = STOCK.history(start=START_DATE_FMT, end=END_DATE_FMT)
            DATA.reset_index(inplace=True)
            DATA.rename(columns={
                "Date": "DATE", "Open": "OPEN", "High": "HIGH", "Low": "LOW", 
                "Close": "CLOSE", "Volume": "VOLUME", "Dividends": "DIVIDENDS", 
                "Stock Splits": "STOCK_SPLITS"
            }, inplace=True)

            DATA['DATE'] = pd.to_datetime(DATA['DATE']).dt.tz_localize(None)
            DATA.sort_values(by="DATE", inplace=True)  # Ensure dates are in ascending order

            # Use PERIOD for periodic investments and REOCCURING_PERIOD_MAP for recurring
            EOP_PERIODIC = DATA.groupby(DATA['DATE'].dt.to_period(PERIOD), as_index=False).agg({'DATE': 'max'})
            EOP_PERIODIC['DATE'] = pd.to_datetime(EOP_PERIODIC['DATE']).dt.tz_localize(None)

            EOP_RECURRING = DATA.groupby(DATA['DATE'].dt.to_period(REOCCURING_PERIOD), as_index=False).agg({'DATE': 'max'})
            EOP_RECURRING['DATE'] = pd.to_datetime(EOP_RECURRING['DATE']).dt.tz_localize(None)

            WATCHLIST_DF.append(DATA.copy())
            EOP_DF.append(EOP_PERIODIC.copy())
            EOP_DF_RECURRING.append(EOP_RECURRING.copy())

        for u, ticker in enumerate(WATCHLIST):
            INPUT_DF = WATCHLIST_DF[u]
            EOP_PERIODIC_DF = EOP_DF[u]
            EOP_RECURRING_DF = EOP_DF_RECURRING[u]
            IIA = INITIAL_INVESTMENT_AMOUNT * WEIGHTS[u]
            PIA = PERIODIC_INVESTMENT_AMOUNT * WEIGHTS[u]

            PIA = PERIODIC_INVESTMENT_AMOUNT * WEIGHTS[u]
            PIA = PERIODIC_INVESTMENT_AMOUNT * WEIGHTS[u]

            INPUT_DF = INPUT_DF.sort_values(by='DATE').reset_index(drop=True)

            SHARES_HELD, INVESTED_CASH, TOTAL_DIVIDENDS, INDIVIDUAL_PORTFOLIO = 0, 0, 0, []

            for i, row in INPUT_DF.iterrows():
                DATE = row['DATE']
                CLOSE_PRICE = row['CLOSE']
                DIVIDEND_PER_SHARE = row['DIVIDENDS']

                # Check if the current date matches EOP dates
                is_periodic_eop_date = DATE in EOP_PERIODIC_DF['DATE'].values
                is_recurring_eop_date = DATE in EOP_RECURRING_DF['DATE'].values

                # Apply Initial Investment
                if INVESTED_CASH == 0:
                    SHARES_PURCHASED = IIA / CLOSE_PRICE
                    SHARES_HELD += SHARES_PURCHASED
                    INVESTED_CASH += IIA

                # Apply Periodic Investments only on EOP_PERIODIC dates
                if is_periodic_eop_date:
                    SHARES_PURCHASED = PIA / CLOSE_PRICE
                    SHARES_HELD += SHARES_PURCHASED
                    INVESTED_CASH += PIA

                # Apply Recurring Investments only on EOP_RECURRING dates
                if is_recurring_eop_date:
                    SHARES_PURCHASED = (REOCCURING_AMOUNT * WEIGHTS[u]) / CLOSE_PRICE
                    SHARES_HELD += SHARES_PURCHASED
                    INVESTED_CASH += (REOCCURING_AMOUNT * WEIGHTS[u])

                # Apply Independent Investments by matching nearest date
                for IND_VALUE, IND_DATE in zip(INDEPENDENT_VALUES, INDEPENDENT_DATES):
                    if abs((DATE - IND_DATE).days) <= 15:  # Match within a 15-day margin
                        SHARES_PURCHASED = (IND_VALUE * WEIGHTS[u]) / CLOSE_PRICE
                        SHARES_HELD += SHARES_PURCHASED
                        INVESTED_CASH += (IND_VALUE * WEIGHTS[u])

                # Calculate Dividends
                if DIVIDEND_PER_SHARE > 0:
                    DIVIDENDS_EARNED = (SHARES_HELD * DIVIDEND_PER_SHARE) * (1-DIVIDENT_TAX_RATE)
                    SHARES_HELD += DIVIDENDS_EARNED / CLOSE_PRICE
                    TOTAL_DIVIDENDS += DIVIDENDS_EARNED  

                # Calculate Portfolio Value
                PORTFOLIO_VALUE = SHARES_HELD * CLOSE_PRICE

                INDIVIDUAL_PORTFOLIO.append({
                    'DATE': DATE.strftime('%Y-%m-%d'),
                    'CASH_INVESTED': round(INVESTED_CASH, 2),
                    'DIVIDENDS_EARNED': round(TOTAL_DIVIDENDS, 2),
                    'PORTFOLIO_VALUE': round(PORTFOLIO_VALUE, 2),
                })

            # Ensure individual portfolios are sorted by ascending dates
            INDIVIDUAL_PORTFOLIO = sorted(INDIVIDUAL_PORTFOLIO, key=lambda x: x["DATE"])
            PORTFOLIO_LIST.append(pd.DataFrame(INDIVIDUAL_PORTFOLIO))
            output[ticker] = INDIVIDUAL_PORTFOLIO  # Add to output by ticker

        # Combine all portfolios into a single view
        COMBINED_VIEW = pd.concat(PORTFOLIO_LIST).sort_values(by="DATE").groupby('DATE', as_index=False).agg({
            'CASH_INVESTED': 'sum',
            'DIVIDENDS_EARNED': 'sum',
            'PORTFOLIO_VALUE': 'sum'
        }).to_dict(orient='records')

        output["all"] = COMBINED_VIEW
        return output