#dependencies
import math
import numpy
from datetime import datetime, timezone
from copy import deepcopy
import time
import MetaTrader5 as mt5 #optional for connection to MetaTrader5


#Condinum
#This class converts candle recognition markups into python objects to facilitate processing
#This comes in handy when trying to describe custom candlestick patterns.  It is a helper class for the CandleWizard class.
#Operators for initialization argument include:
    # x = internal comparison
    # xx = external comparison
    # $ = pointer/reference
    # <,<=,>,>=,== meanings remain the same
    # use | to seperate multiple expressions    
	# use [] to group expressions
	# use ; for , such that expressions such as max($1,$2,$3) becomes max[$1;$2;$3]
#example 1; Condinum('$1|<[$2-[abs[$2-$3]/2]]'); this expression creates a Condinum object:
	# $1 = assigns the value of the Condinum with the reference number 1 => Condinum($1) 
	# | = seperator
	# <[$2-[abs[$2-$3]/2] = this expression simply indicates that this value of the Condinum($1) must be less than half of the absolute difference between the value of Condinum($2) and value of Condinum($3) when substracted from the value of Condinum($2)
#example 2; Condinum('$1|x2')
	# $1 = assigns the value of the Condinum with the reference number 1 => Condinum($1) 
	# | = seperator
	# xx2 = this indicates that the value of the Condinum must be twice the value of another Condinum (labeled xx1) in another candle
#example 3; Condinum('$2|x3|>=$1*0.8')
	# $2 = assigns the value of the Condinum with the reference number 2 => Condinum($2) 
	# | = seperator
	# x3 = this indicates that this Condinum must be thrice the value of the Condinum (labeled x1) in the same candle 
	# | = seperator
	# >=$1*0.8 = this indicates that this Condinum must be greater than or equal to the product of 0.8 and Condinum($1)
class Condinum:
    def __init__(self, value):
        self.v = self.le = self.ge = self.eq = self.ne = self.xx = self.lt = self.gt = self.x = self.rp = None
        self.value = str(value)
        value = str(value).split('|')
        for v in value:
            v = v.strip()
            if len(v) == 0: continue
            v = v.replace('[', '('); v = v.replace(']', ')'); v = v.replace(';', ',')
            vv = ''.join([n for n in v if n in '+-0.123456789$*/)(maxinabs,'])
            if vv.find('$') == -1 and vv.find('x') == -1 and vv.find('xx') == -1 and vv.find('.') != -1: vv = float(vv)
            elif vv.find('$') == -1 and vv.find('x') == -1 and vv.find('xx') == -1: vv = int(vv)                
            if v[:2].find('<=') != -1: self.le = vv
            elif v[:2].find('>=') != -1: self.ge = vv
            elif v[:2].find('==') != -1: self.eq = vv
            elif v[:2].find('!=') != -1: self.ne = vv
            elif v[:2].find('xx') != -1: self.xx = float(vv[2:])
            elif v[:1].find('<') != -1: self.lt = vv
            elif v[:1].find('>') != -1: self.gt = vv
            elif v[:1].find('x') != -1: self.x = float(vv[1:])
            elif v[:1].find('$') != -1: self.rp = vv
            else: self.v = vv

    def replace(self, rp, rpv):
        rpv = str(rpv)
        di = dict(self.__dict__)
        for k in di:
            if k == 'rp': continue
            if type(di[k]) == str:
                di[k] = di[k].replace(rp, rpv)
                setattr(self, k, di[k])

    def __eval(self, exp):
        exp = str(exp)
        try:
            r = eval(exp)
        except:
            return False
        else:
            return r

    def compare(self, other, checkzero=False):
        if self.le != None and other > self.__eval(self.le): return False
        if self.ge != None and other < self.__eval(self.ge): return False
        if self.eq != None and other != self.__eval(self.eq): return False
        if self.ne != None and other == self.__eval(self.ne): return False
        if self.lt != None and other >= self.__eval(self.lt): return False
        if self.gt != None and other <= self.__eval(self.gt): return False
        if checkzero == False and self.v != None and self.v != 0 and other != self.v: return False
        elif checkzero == True and self.v != None and other != self.v: return False
        return True
   
    def __repr__(self):
        #di = dict(self.__dict__)
        #return di.__repr__()
        return self.value
    
       
#Chandler
#This class converts sample ohlcv data into a suitable python object to facilitate processing
class Chandler:
    def __init__(self, t, o, h, l, c, v):
        self.datetime = str(datetime.fromtimestamp(t))
        self.open = float(o)
        self.high = float(h)
        self.low = float(l)
        self.close = float(c)
        self.volume = float(v)
        self.body = abs(self.close - self.open)
        self.uppershadow = (self.high - self.close) if self.close >= self.open else (self.high - self.open)
        self.lowershadow = (self.open - self.low) if self.close >= self.open else (self.close - self.low)
        self.shadow = (self.uppershadow + self.lowershadow) / 2
        self.candletype = 1 if self.close >= self.open else -1
        self.whole = self.high - self.low
        
    def data(self,aslist=False,getall=True):
        if getall == True:
            data = dict(self.__dict__)
        else:
            data = {'datetime':self.datetime,'open':self.open,'high':self.high,'low':self.low,'close':self.close,'volume':self.volume}
        if aslist == True:
            data = list(data.values())
        return data
   
    def __repr__(self):
        di = dict(self.__dict__)
        return di.__repr__()
    
    
#CandleWizard
#This class searches for candle patterns in a given set of candle data
#Candle data is built from the Chandler class
#Each value in a given pattern is a typical Condinum
	#pattern format = [pattern_name, indication(+1 or -1), patterns(trends and/or candles)]
		#indication = a naive effort to assign a weight denoting what the effect of the pattern will be on future data (+1 means rise while -1 means fall)
		#patterns =
			# (1 value) = (trendtype(-1,0,+1))
			# (4 values) = (open, high, low, close)
			# (5 values) = (candletype(-1,0,+1), uppershadow%, body%, lowershadow%, whole size)
			# (8 values) = (open, high, low, close, uppershadow%, body%, lowershadow%, whole size)
			# (9 values) = (candletype(-1,0,+1), open, high, low, close, uppershadow, body, lowershadow, whole size)
# +1 = green candle or uptrend where applicable
# -1 = red candle or downtrend where applicable
# 0 = means any number, any candle (+1 or -1) or is used to denote a ranging trend where applicable
class CandleWizard():
	#patterns to search for:
	#usage of defaultpatterns is at user's risk; feel free to edit, delete or add
   defaultpatterns = [
        [ 'Bearish Marubozu', -1, ['(0, 0, 0, 0, $1), (0, 0, 0, 0, $2), (0, 0, 0, 0, $3), (-1, 0, >80, 0, >=max[$1;$2;$3])'] ],
        [ 'Bearish Marubozu', -1, ['(-1, 0, >=70, 0, 0)'] ],
        [ 'Bullish Marubozu', 1, ['(0, 0, 0, 0, $1), (0, 0, 0, 0, $2), (0, 0, 0, 0, $3), (+1, 0, >80, 0, >=max[$1;$2;$3])'] ],
        [ 'Doji', 0, ['(0, 0, 0, 0, $1), (0, 0, 0, 0, $2), (0, 0, 0, 0, $3), (0, >20, <=5, >20, >=[[$1+$2+$3]/3])'] ],
        [ 'Evening Star', -1, ['($1, $3, $4, >$1), (0, >20, <=10, >20, 0), (>$2, 0, 0, $2|<[$3-[abs[$3-$4]/2]])'] ],
        [ 'Morning Star', 1, ['($1, $3, $4, <$1), (0, >20, <=10, >20, 0), (<$2, 0, 0, $2|>[$3-[abs[$3-$4]/2]])'] ],
        [ 'Hanging Man', -1, ['(0,$2,$3,0), (0,>$2,0,0), (>$1,0,0,$1|<[$2-[abs[$2-$3]/2]])', '(+1), (-1, <=5, >5|x1, x3, 0), (0,0,0,0)']], 
        [ 'Hammer', 1, ['(0,$2,$3,0), (0,0,<$3,0), (<$1,0,0,$1|>[$2-[abs[$2-$3]/2]])', '(-1), (0, <=5, >5|x1, x3, 0), (0,0,0,0)'] ],
        [ 'Shooting Star', -1, ['(0,$2,$3,0), (0,>$2,0,0), (>$1,0,0,$1|<[$2-[abs[$2-$3]/2]])', '(+1), (0, x3, >5|x1, <=5, 0), (0,0,0,0)']], 
        [ 'Inverted Hammer', 1, ['(0,$2,$3,0), (0,0,<$3,0), (<$1,0,0,$1|>[$2-[abs[$2-$3]/2]])', '(-1), (+1, x3, >5|x1, <=5, 0), (0,0,0,0)'] ],
        [ 'Bearish Engulfing', -1, ['(+1, 0, >=60, 0, xx1), (-1, 0, >80, 0, xx4)'] ],
        [ 'Bullish Engulfing', 1, ['(-1, 0, >=60, 0, xx1), (+1, 0, >80, 0, xx4)'] ],
        [ 'Tweezer Tops', -1, ['(0,$1,$2,0), (0,>$1*0.9|<$1*1.1,>$2*0.9|<$2*1.1,0)', '(+1), (+1, $2|>=47.5, 0, <=5, $1), (-1, >$2*0.5|<$2*1.5|>=47.5, 0, <=5, >$1*0.5|<$1*1.5)'] ],
        [ 'Tweezer Bottoms', 1, ['(0,$1,$2,0), (0,>$1*0.9|<$1*1.1,>$2*0.9|<$2*1.1,0)', '(-1), (-1, <=5, 0, $2|>=47.5, $1), (+1, <=5, 0, >$2*0.5|<$2*1.5|>=47.5, >$1*0.5|<$1*1.5)'] ],
        [ 'Three black crows', -1, ['(-1, 0, >=35, 0, xx1), (-1, 0, >60, 0, $1|xx2), (-1, 0, >80, 0, xx2|<$1*0.8)'] ],        
        [ 'Three white soldiers', 1, ['(+1, 0, >=35, 0, xx1), (+1, 0, >60, 0, $1|xx2), (+1, 0, >80, 0, xx2|<$1*0.8)'] ],        
    ]

    def __init__(self, candles, span=5):
        self.history = candles[-(span):]
        self.span = span #minimum number of candles to consider for trend recognition
        self.patterns = self.parse(deepcopy(self.defaultpatterns))
        
    def parse(self, patterns):
        for i in range(len(patterns)):
            for j in range(len(patterns[i][2])):
                patterns[i][2][j] = patterns[i][2][j].strip() + ','
                s = patterns[i][2][j].split('(')
                groups = []; group = []
                for cp in s:
                    cp = cp.strip()
                    if cp == '': continue
                    cp = cp.split(',')
                    for p in cp:
                        p = p.strip()
                        if p == '': continue
                        if p[len(p)-1] == ')':
                            group.append(Condinum(p[:-1].strip()))
                            groups.append(group)
                            group = []
                        else:
                            group.append(Condinum(p))
                patterns[i][2][j] = groups
        return patterns

    def onlivedata(self, livedata, stable=True):
        history = deepcopy(self.history)
        self.history.pop(0)
        self.history.append(livedata)
        results = []
        upward = 0; downward = 0; check = False
        for p in self.patterns:
            found = False
            for p2i in p[2]:
                found = self.check(p2i)
                if found == False: break
            if found != False:
                if p[1] == 1:
                    upward = upward + 1
                elif p[1] == -1:
                    downward = downward + 1
                else:
                    check = True
                results.append(p[0] + str(tuple(found)))
        if stable != True:
            self.history = history
		#naive effort to denote what the effect of the current patterns will be on future data
        if (upward + downward) == 0:
            if check == True:
                results.append('SUMMARY(CHECK)')
                return len(results)-1, "\n".join(results)
            return 0, 'No special candles or patterns found!'
        elif upward > downward:
            if check == True:
                results.append('SUMMARY(CHECK/RISE)')
            else:
                results.append('SUMMARY(RISE)')
            return len(results)-1, "\n".join(results)
        elif upward < downward:
            if check == True:
                results.append('SUMMARY(CHECK/FALL)')
            else:
                results.append('SUMMARY(FALL)')
            return len(results)-1, "\n".join(results)
        else:
            if check == True:
                results.append('SUMMARY(CHECK/NONE)')
            else:
                results.append('SUMMARY(NONE)')
            return len(results)-1, "\n".join(results)            

    def check(self, candlepatterns):
        candlepatterns = deepcopy(candlepatterns)
        #process candles
        if len(candlepatterns) == 0:
            raise Exception('Cannot check against null pattern')
            return False
        #get history
        history = []
        ind = -1
        contains_trend = False
        for i in range(len(candlepatterns)-1, -1, -1):
            if len(candlepatterns[i]) == 1:
                history.append([ self.history[::-1][ind+3], self.history[::-1][ind+2], self.history[::-1][ind+1] ])
                ind = ind + 3
                contains_trend = True
            else:
                if contains_trend == True:
                    raise Exception('Unable to check for trends after candles')
                    return False
                ind = ind + 1
                history.append(self.history[::-1][ind])
        if len([cp for cp in candlepatterns if len(cp) == 4 or len(cp) == 5 or len(cp) == 8 or len(cp) == 9]) == 0:
            raise Exception('Pattern must contain candles')
            return False
        history = list(reversed(history))
        for i in range(len(candlepatterns)):
            candle = history[i]
            if len(candlepatterns[i]) == 1:
                #1(trend type 0, +1, -1)
                mindiff =  (candle[0].whole + candle[1].whole + candle[2].whole) / 3
                if abs(candle[2].close - candle[0].close) <= mindiff:
                    r = 0
                elif candle[2].close > candle[0].close:
                    r = 1
                else:
                    r = -1
                history[i] = [r, candle[0].datetime, candle[2].datetime]
            elif len(candlepatterns[i]) == 4:
                #4(open, high, low, close)
                history[i] = [candle.open,candle.high,candle.low,candle.close,candle.datetime]
            elif len(candlepatterns[i]) == 5:
                #5(candletype, uppershadow%, body%, lowershadow%, whole size)
                u = (candle.uppershadow / candle.whole) * 100
                b = (candle.body / candle.whole) * 100
                l = (candle.lowershadow / candle.whole) * 100
                history[i] = [candle.candletype,u,b,l,candle.whole,candle.datetime]
            elif len(candlepatterns[i]) == 8:
                #8(open, high, low, close, uppershadow%, body%, lowershadow%, whole size)
                u = (candle.uppershadow / candle.whole) * 100
                b = (candle.body / candle.whole) * 100
                l = (candle.lowershadow / candle.whole) * 100
                history[i] = [candle.open,candle.high,candle.low,candle.close,u,b,l,candle.whole,candle.datetime]
            elif len(candlepatterns[i]) == 9:
                #9(candletype, open, high, low, close, uppershadow, body, lowershadow, whole size)
                history[i] = [candle.candletype,candle.open,candle.high,candle.low,candle.close,candle.uppershadow,candle.body,candle.lowershadow,candle.whole,candle.datetime]
            else:
                raise Exception('Encountered invalid pattern while checking')
                return False
        #resolve unknowns
        for i in range(len(candlepatterns)):
            for j in range(len(candlepatterns[i])):
                if candlepatterns[i][j].rp != None:
                    for k in range(len(candlepatterns)):
                        for l in range(len(candlepatterns[k])):
                            candlepatterns[k][l].replace(candlepatterns[i][j].rp, history[i][j])
                if candlepatterns[i][j].xx != None and candlepatterns[i][j].xx == 1:
                    for k in range(len(candlepatterns)):
                        for l in range(len(candlepatterns[k])):
                            if candlepatterns[k][l].xx != None:
                                xxv = history[i][j] * candlepatterns[k][l].xx
                                candlepatterns[k][l].ge = xxv if candlepatterns[k][l].ge == None else max(candlepatterns[k][l].ge, xxv)
                                candlepatterns[k][l].xx = None
                if candlepatterns[i][j].x != None and candlepatterns[i][j].x == 1:
                    for l in range(len(candlepatterns[i])):
                        if candlepatterns[i][l].x != None:
                            xv = history[i][j] * candlepatterns[i][l].x
                            candlepatterns[i][l].ge = xv if candlepatterns[i][l].ge == None else max(candlepatterns[i][l].ge, xv)
                            candlepatterns[i][l].x = None
        #compare
        daterange = []
        result = True
        for i in range(len(candlepatterns)):
            if len(history[i]) > 3:
                daterange.append(history[i][len(history[i])-1])
                checkzero = False
            else:
                dr = history[i][1] + '--' + history[i][2]
                daterange.append(dr)
                checkzero = True
            for j in range(len(candlepatterns[i])): 
                result = candlepatterns[i][j].compare(history[i][j], checkzero)
                if result == False: break
            if result == False: break
        if result == True:
            return daterange
        return False

    def __repr__(self):
        return 'CandleWzard object (' + str(id(self)) + ')'