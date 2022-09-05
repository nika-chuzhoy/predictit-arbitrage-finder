import numpy as np
import json
import requests
import pandas as pd


"""
Calulates the profit/loss from buying a certain set of no shares,
given which share will evaluate to yes.

Arguments:
price_array: the prices of the no shares
counts_array: the quantity purchased of each no share
yes_index: the index of the share which will evaluate to yes 
within the price and counts arrays
"""
def gen_profit(price_array, counts_array, yes_index):
    
    yes_x = counts_array[yes_index]
    yes_share = price_array[yes_index]
    
    winnings = sum(counts_array) - yes_x
    
    total_fees = 0
    for i in range(len(counts_array)):
        cur_fee =  0.1 * counts_array[i] * (1 - price_array[i])
        total_fees += cur_fee
        
    yes_fee = 0.1 * yes_x * (1 - yes_share)
    
    total_fees -= yes_fee
    
    investment = sum(np.multiply(price_array, counts_array))
    
    return winnings - total_fees - investment


"""
Finds the minimum profit over every set of possible outcomes,
for a given set of no shares purchased.
This amount is automatically credited by PredictIt.
"""
def gen_min_profit(price_array, counts_array):
    min_prof = 100000
    for i in range(len(price_array)):
        min_prof = min(min_prof,gen_profit(price_array, counts_array, i))
        
    return min_prof


"""
Finds the ideal ratio of no shares to purchase given the prices of the no shares.
"""

def get_ratio(prices):
    equations = []
    vals = []
    
    #create coefficient array for first equation
    firstcoeffs = []
    firstval = prices[0]
        
    for s in range(1, len(prices)):
        firstcoeffs.append(0.9 * (1 - prices[s]))
    
    #create coefficient array for all subsequent equations
    for i in range(1, len(prices)):
        coefficients = []
        
        for j in range(1,i):
            coefficients.append(0.9 * (1 - prices[j]))
        
        coefficients.append(-prices[i])
        
        for k in range(i + 1, len(prices)):
            coefficients.append(0.9 * (1 - prices[k]))
            
        const = -(0.9 * (1 - prices[0]))
        
        #subtract first equation from current equation
        equations.append(np.subtract(coefficients,firstcoeffs))
        vals.append(const - firstval)
    
    ratio = np.insert((np.linalg.solve(equations, vals)),0,1)
    
    return ratio


"""
Finds the smallest possible set of no shares one can purchase and still make a profit,
given the prices of the no shares.
"""

def get_share_quants(prices):
    ratio = get_ratio(prices)
    for i in range(1,850):
        shares = np.around(np.multiply(i,ratio))
        profit = gen_min_profit(prices,shares)
        if(profit > 0):
            return shares


"""
Displays information about purchasing options and anticipated profit.
"""
def print_ratio(prices):
    
    ratio = get_ratio(prices)
    print("Optimal ratio: \n",ratio)
    
    profit = gen_min_profit(prices, ratio)
    print("Profit at optimal ratio: \n",profit)
    
    share_quants = get_share_quants(prices)
    
    if(share_quants is not None):
        print("Minimum profitable set of share quantities to purchase:\n", share_quants)
        print("Profit at quantities:\n", gen_min_profit(prices,share_quants))
    
    else:
        print("The arbitrage may not be actionable.")


"""
Extracts relevant information on markets available on Predictit.
Returns a dataframe with the prices of all no shares by market.
"""
def read_data():
    response_API = requests.get('https://www.predictit.org/api/marketdata/all/')
    data = json.loads(response_API.text)
    
    #clean data
    contracts = []
    for i in range(len(data['markets'])):
        cur_contracts_list = data['markets'][i]['contracts']
        for j in range(len(cur_contracts_list)):
            new_contract = {**{'market title': data['markets'][i]['name']},**cur_contracts_list[j]}
            contracts.append(new_contract)

    temp_df = pd.json_normalize(contracts)
    final_df = temp_df[['market title','bestBuyNoCost']]
    return final_df


"""
Prints all available arbs on PredictIt.
"""
def display_arbs():
    df = read_data()
    old_name = ""
    for i in range(len(df)):
    
        new_name = df.iloc[i]["market title"]
        same_market = df.loc[df['market title'] == new_name]
        nos = same_market["bestBuyNoCost"].to_numpy()
        nos = np.delete(nos,np.where(np.isnan(nos)))
    
        if(new_name != old_name):
            if(len(nos) > 1):
                profit = gen_min_profit(nos,get_ratio(nos))
                if(profit > 0):
                    print("Market name:\n", new_name)
                    print("Prices:\n", nos)
                    print_ratio(nos)
                    print()
            
        old_name = new_name


display_arbs()




