# Calculating gain/loss plus investment #

## Definitions ##

1. **ASSET**: the amount of a specific crypto currency.  
2. **INVESTMENT**: the value in fiat of a given asset at a specific point in time. Investment consist of Deposit, Withdral, Gain and Loss.  
3. **ACTION**:
    * **SWAP**: affect mainly assets but there is always a gain or loss that would affect investment as well. Swap consists of at least two transactions plus a gain/loss and possibly a Fee transaction.  
    * **DEPOSIT & WITHDRAWL**: affect both asset and investment.  
    * **FEE & INTEREST**: affect asset only.  
    * **GAIN & LOSS**: affect only investment.  
    * **TRANSFER**: affect mostly wallet but it may affect assets by Fees and always comes in pairs.  

## Process ##

1. Get data  
2. We loop through each trasction, check **action_type** and updating TRACKED_INVESTMENT
    * if "DEPOSIT" or "WITHDRAWL" we add/subtract to/from 'TRACKED_INVESTMENT["investment"]'
    * if "FEE", "INTEREST", "MINING" or "ADJUSTMENT" we add/subtract to/from asset 'TRACKED_INVESTMENT["amount"]'
    * if "SWAP" we calculate
        * we are going to update the investment column
        * **IS THIS A COMPLETE OR PARTIAL SWAP?**
            * if SUM the src coin and the dest coin is **ZERO**, is considered complete
            * if SUM the src coin and the dest coin coin is **POSITIVE** is considered partial
            * if SUM the src coin and the dest coin is **NEGATIVE** we need to raise an exception

        * The investment as result of swap, the dest_amount has a value in fiat representing an investment. We should update the src coin with a negative investment and the dest coint with a positive investment.

        * substract "'TRACKED_INVESTMENT["investment"]' minus "dest investment".
            * if the value is positive, we need to register a "GAIN" since we had some profit and add it to 'TRACKED_INVESTMENT["investment"]'.
            * if the value is negative, we need to register a "LOSS" since we had some loss and add it to 'TRACKED_INVESTMENT["investment"]'.
            * if the value is equal to the investment, we DON'T do anything.
