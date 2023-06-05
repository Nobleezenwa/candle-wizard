## candle-wizard

An unsupervised machine learning feed tool written in Python for recognizing and classifying trading chart patterns. The tool features an internal custom candle pattern recognition schema.

**Dependencies**

- math
- numpy
- datetime
- copy
- time

**Classes**

- Condinum
- Chandler
- CandleWizard

**Condinum**

This class converts candle recognition markups into python objects to facilitate processing
This comes in handy when trying to describe custom candlestick patterns. It is a helper class for the CandleWizard class.
Operators for initialization argument include:

- x = internal comparison
- xx = external comparison
- $ = pointer/reference
- <,<=,>,>=,== meanings remain the same
- use | to seperate multiple expressions    
- use [] to group expressions
- use ; for , such that expressions such as max($1,$2,$3) becomes max[$1;$2;$3]

​	**Example 1**
​	`cndnm = Condinum('$1|<[$2-[abs[$2-$3]/2]]')`
​	This expression creates a Condinum object:
​		`$1` = assigns the value of the Condinum with the reference number 1 => Condinum($1) 
​		`|` = seperator
​		`<[$2-[abs[$2-$3]/2]` = this expression simply indicates that the value of this Condinum($1) must be less than half of the absolute difference between the value of Condinum($2) and value of Condinum($3) when it is substracted from the value of Condinum($2)
​	**Example 2**
​	`cndnm = Condinum('$1|x2')`
​		`$1` = assigns the value of the Condinum with the reference number 1 => Condinum($1) 
​		`|` = seperator
​		`xx2` = this indicates that the value of this Condinum must be twice the value of another Condinum (labeled xx1) in another candle
​	**Example 3**
​	`cndnm = Condinum('$2|x3|>=$1*0.8')`
​		`$2` = assigns the value of the Condinum with the reference number 2 => Condinum($2) 
​		`|` = seperator
​		`x3` = this indicates that this Condinum must be thrice the value of the Condinum (labeled x1) in the same candle
​		`|` = seperator
​		`>=$1*0.8` = this indicates that this Condinum must be greater than or equal to the product of 0.8 and Condinum($1)

**Chandler**

This class converts sample ohlcv data into a suitable python object to facilitate processing
		`candle = Chandler(timestamp, open, high, low, close, volume)`

**CandleWizard**

This class searches for candle patterns in a given set of candle data
Candle data is built from the Chandler class
Each value in a given pattern is a typical Condinum
	pattern format = [pattern_name, pattern_indication(+1 or -1), patterns(trends and/or candles)]
		pattern_name = display name e.g. Three Black Crows
		indication = a naive effort to assign a weight denoting what the effect of the pattern will be on future data (+1 means rise while -1 means fall)
		patterns = 
			(1 value) = (trendtype(-1,0,+1))
			(4 values) = (open, high, low, close)
			(5 values) = (candletype(-1,0,+1), uppershadow%, body%, lowershadow%, whole size)
			(8 values) = (open, high, low, close, uppershadow%, body%, lowershadow%, whole size)
			(9 values) = (candletype(-1,0,+1), open, high, low, close, uppershadow, body, lowershadow, whole size)
	+1 = green candle or uptrend where applicable
	-1 = red candle or downtrend where applicable
	 0 = means any number, any candle (+1 or -1) or is used to denote a ranging trend where applicable

**Example**

The following example requires the Python MetaTrader5 library and an MT5 trading account

```python
import cwiz
import MetaTrader5 as mt5

ID = 000000 #replace with your MT5 account ID
PASSWORD = '***********' #replace with your MT5 account password
SERVER = 'XXXXXXXXXXX' #replace with your MT5 broker's server name

if not mt5.initialize(login=ID, password=PASSWORD, server=SERVER, timeout=15000):
    print("initialize() failed, error code =",mt5.last_error())
    quit()

while True:
    symbol = input('Enter symbol name or just press Enter to exit: ')
    if symbol == '': break
    try:
        history = []
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 1, 500)
        rates = list(rates)
        print('Length of rates recieved:', len(rates))
        for rate in rates:
            history.append(Chandler(int(rate[0]),float(rate[1]),float(rate[2]),float(rate[3]),float(rate[4]),float(rate[7])))
        cwiz = CandleWizard(candles=history[:20], span=14)
        print(symbol, '===>', 'RESULT******************************')
        h = history[20:]
        c = 0
        f = 0
        for i in range(len(h)):
            c = c + 1
            r = cwiz.onlivedata(h[i])
            if r[0] > 0:
                f = f + 1
                print(r)
                print()
        del cwiz
    except:
        print('error here!!!')
    print('DONE************************************')
    print('found =', f)
    print('total searches =', c)
    print('result =', str(round((f/c) * 100, 2))+'%')
    
mt5.shutdown()

print('done')
```

