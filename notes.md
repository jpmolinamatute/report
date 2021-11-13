# Calculating gain/loss plus investment #

## Definitions ##

1. **ASSET**: the amount of a specific crypto currency.  
2. **INVESTMENT**: the value in fiat of a given asset at a specific point in time.  
3. **ACTION**:
    * **SWAP**: affect mainly assets but there is always a gain or loss that would affect investment as well. Swap consists of at least two transactions plus a gain/loss and possibly a Fee transaction.  
    * **DEPOSIT & WITHDRAWL**: affect both asset and investment.  
    * **FEE & INTEREST**: affect asset only.  
    * **GAIN & LOSS**: affect only investment.  
    * **TRANSFER**: affect mostly wallet but it may affect assets by Fees and always comes in pairs.  

## Steps ##

1. Get data ("SWAP", "DEPOSIT", "WITHDRAW")  
2. We loop through each trasction and check **action_type**.  
    * if "DEPOSIT" we add to investment cache
    * if "WITHDRAWL" we subtract from investment cache
    * if "SWAP" we calculate
        * we are going to update the investment column
        * **IS THIS A COMPLETE OR PARTIAL SWAP?**
            * if SUM of negative coin is **ZERO**, is considered complete
            * if SUM negative coin is **POSITIVE** is considered partial
            * if SUM negative coin is **NEGATIVE** we need to raise an exception
        * the "current" amount of each coin.
        * the investment until this point assigned to this coin.
        * update the negative coin with a negative investment
        * update the positive coin with its value in fiat
        * compare the investment of the negative coin with the value in fiat of the positive coin.
            * if the value is greater than the investment, we need to register a "GAIN" since we had some profit.
            * if the value is less than the investment, we need to register a "LOSS" since we had some loss.
            * if the value is equal to the investment, we DON'T do anything.
