def oddsToDecimal(odds):
    values = odds.split(":")
    numerator = float(values[0])
    denominator = float(values[1])
    decimal = ((numerator / denominator) + 1)
    eachWayDecimal = (((numerator / 5) / denominator) + 1)
    return decimal, eachWayDecimal

def resolveStake(stake, eachway):
    if eachway:
        return stake * 2
    return stake

def resolveBetValue(place,stake,odds,eachWay):
    decimal, eachWayDecimal = oddsToDecimal(odds)
    betValue = 0
    
    if eachWay == 0:
        if place == 1:
            betValue = stake * decimal
        else:
            betValue = 0
    elif eachWay == 1:    
        winWinnings = stake * decimal
        placeWinnings = stake * eachWayDecimal

        if place == 1:
            betValue = winWinnings + placeWinnings
            
        elif place == 2 or place == 3:
            betValue = placeWinnings
    else:
        betValue = 0

    return betValue
            
def previewCalc(stake,odds):
    singleWin = resolveBetValue(1,stake,odds,0)
    eachWayWin = resolveBetValue(1,stake,odds,1)
    eachWayPlace = resolveBetValue(2,stake,odds,1)

    resultsPreview = {"singleWin" : singleWin, "eachWayWin" : eachWayWin, "eachWayPlace" : eachWayPlace}

    return resultsPreview