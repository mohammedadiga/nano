import ccxt
import schedule
import requests
import time
import pandas as pd
import talib as ta
from datetime import datetime

exchange = ccxt.binance({
    "apiKey": 'mbgw4LMv8eJwBc0hgaG8l5O4DGNyYrGGyWSJtLpUg5bXVCgSFRrnZI1GRQRBZ7K1',
    "secret": 'XhyTP8xHCAGp3VTP6yPMxTG0PohFsr0punWbu6S3QbraH3erEbYiqIUUv25PdVVu'
})

token = "1596704623:AAGRb742fuV_ssqkQx32d6MID5Z0nkmcGq8"
chat_id = "655845780"


def str(df):
    T = df['timeframe']
    O = df['open']
    H = df['high']
    L = df['low']
    C = df['close']
    V = df['volume']


    df['price'] = df['close']

    df['RB'] = C - O
    df['us'] = 0
    df['ls'] = 0

    for i in range(0 ,df.index.stop):
        if df['RB'][i] > 0:
            df.loc[i,'us'] = df['high'][i] - df['close'][i]
        else: 
            df.loc[i,'us'] = df['high'][i] - df['open'][i]
            
    for i in range(0 ,df.index.stop):
        if df['RB'][i] > 0:
            df.loc[i,'ls'] = df['open'][i] - df['low'][i]
        else: 
            df.loc[i,'ls'] = df['close'][i] - df['low'][i]

    df['factor'] = ta.RSI(df['price'], 3)

    uthres = 80
    lthres = 15 
    lb = 10

    df['doji2'] = 0
    df['uptrend'] = 0
    df['downtrend'] = 0
    df['doji2'] = df['RB'] == 0
 
    for i in range(1 ,df.index.stop):
        y = i - 1
        df.loc[i,'uptrend'] = (df['RB'][i] > 0 ) | (df['doji2'][i] == True and df['RB'][y] > 0)
        df.loc[i,'downtrend'] = (df['RB'][i] < 0 ) | (df['doji2'][i] == True and df['RB'][y] < 0)
               
    # // One-day bullish candlestick patterns (Morris, 2006):
    for con in range(1 ,df.index.stop):
        i = con - 1
        df.loc[con,'wm'] = H[i] == C[i] and C[i] > O[i] and O[i] == L[i] 
        df.loc[con,'cwm'] = H[i] == C[i] and C[i] > O[i] and O[i] > L[i] 
        df.loc[con,'owm'] = H[i] > C[i] and C[i] > O[i] and O[i] == L[i]
        df.loc[con,'lwc'] = H[i] > C[i] and C[i] > O[i] and O[i] > L[i]
        df.loc[con,'dd']  = H[i] == C[i] and C[i] == O[i] and O[i] > L[i]
        df.loc[con,'wpu'] = H[i] == C[i] and C[i] > O[i] and O[i] > L[i] and df.ls[i] > 2 * df.RB[i]
        df.loc[con,'bpu'] = H[i] == O[i] and O[i] > C[i] and C[i] > L[i] and df.ls[i] > 2 * df.RB[i]

    # // One-day bearish candlestick patterns:
    for con in range(1 ,df.index.stop):
        i = con - 1
        
        df.loc[con,'bm']  = H[i] == O[i] and O[i] > C[i] and C[i] == L[i]
        df.loc[con,'cbm'] = H[i] > O[i] and O[i] > C[i] and C[i] == L[i]
        df.loc[con,'lbc'] = H[i] > O[i] and O[i] > C[i] and C[i] > L[i]
        df.loc[con,'obm'] = H[i] == O[i] and O[i] > C[i] and C[i] > L[i]
        df.loc[con,'gd']  = H[i] > O[i] and O[i] == C[i] and C[i] == L[i]
        df.loc[con,'bss'] = H[i] > O[i] and O[i] > C[i] and C[i] == L[i] and df.us[i] > 2*df.RB[i]
        df.loc[con,'wss'] = H[i] > C[i] and C[i] > O[i] and O[i] == L[i] and df.us[i] > 2*df.RB[i]

    # // Two-day bullish candlestick patterns:
    for con in range(2 ,df.index.stop):
        i = con - 1
        y = con - 1
        
        df.loc[con,'hp'] = O[i] > O[y] and O[y] > C[y] and C[y] > C[i] and df.downtrend[con] == True
        df.loc[con,'bulle'] = C[y] > O[i] and O[i] > C[i] and C[i] > O[y] and df.downtrend[con] == True
        df.loc[con,'pl']    = O[i] > C[y] and C[y] > L[i] and L[i] > O[y] and C[y] > 0.5*(O[i] + C[i]) and df.downtrend[con] == True
        df.loc[con,'bullh'] = (O[i] > C[y] and C[y] > O[y] and O[y] > C[i] and df.RB[i] > df.RB[y] and df.downtrend[con] == True) or (C[i] > C[y] and C[y] > O[y] and O[y] > O[i] and df.RB[i] > df.RB[y] and df.downtrend[con] == True)
        df.loc[con,'bullk'] = C[y] > O[y] and O[y] > O[i] and O[i] > C[i] and df.downtrend[con] == True

    # // Two-day bearish candlestick patterns:
    for con in range(2 ,df.index.stop):
        i = con - 1
        y = con - 2
        
        df.loc[con,'dh']    = C[i] > C[y] and C[y] > O[y] and O[y] > O[i] and df.uptrend[con] == True
        df.loc[con,'beare'] = O[y] > C[i] and C[i] > O[i] and O[i] > C[y] and df.uptrend[con] == True
        df.loc[con,'dcc']   = O[y] > H[i] and H[i] > C[y] and C[y] > O[i] and C[y] < 0.5*(O[i] + C[i]) and df.uptrend[con] == True
        df.loc[con,'bearh'] = (C[i] > O[y] and O[y] > C[y] and C[y] > O[i] and df.RB[i] > df.RB[y] and df.uptrend[con] == True ) or (O[i] > O[y] and O[y] > C[y] and C[y] > C[i] and df.RB[i] > df.RB[y] and df.uptrend[con] == True)
        df.loc[con,'beark'] = C[i] > O[i] and O[i] > O[y] and O[y] > C[y] and df.uptrend[con] == True

    # // Three-day bullish candlestick patterns:
    for con in range(3 ,df.index.stop):
        i = con - 1
        y = con - 2
        x = con - 3
        
        df.loc[con,'tws'] = C[i] > O[i] and C[y] > O[y] and C[x] > O[x] and (C[x] > C[y] and C[y] > C[i]) and (C[i] > O[y] and O[y] > O[i]) and (C[y] > O[x] and O[x] > O[y] and df.downtrend[con] == True)
        df.loc[con,'tiu'] = O[i] > C[i] and (O[i] >= O[y] and O[y] > C[i]) and O[i] > C[y] and C[y] >= C[i] and C[x] > O[x] and (C[x] > O[i] and df.downtrend[con] == True)
        df.loc[con,'tou'] = O[i] > C[i] and (C[y] >= O[i] and O[i] > C[i] and C[i] >= O[y]) and abs(C[y] - O[y]) > abs(C[i] - O[i]) and C[x] > O[x] and (C[x] > C[y] and df.downtrend[con] == True)
        df.loc[con,'ms']  = O[i] > C[i] and abs(O[y] - C[y]) > 0 and C[i] > C[y] and C[i] > O[y] and C[x] > O[x] and (C[x] > 0.5 * (O[i] + C[i]) and df.downtrend[con] == True)

    # // Three-day bearish candlestick patterns:
    for con in range(3 ,df.index.stop):
        i = con - 1
        y = con - 2
        x = con - 3
        
        df.loc[con,'tbc'] = O[i] > C[i] and O[y] > C[y] and O[x] > C[x] and (C[i] > C[y] and C[y] > C[x]) and (O[i] > O[y] and O[y] > O[x]) and (O[i] > O[y] and O[y] > C[i]) and (O[y] > O[x] and O[x] > C[y] and df.uptrend[con])
        df.loc[con,'tid'] = C[i] > O[i] and C[i] > O[y] and O[y] >= O[i] and (C[i] >= C[y] and C[y] > O[i]) and O[x] > C[x] and (O[y] > C[x] and df.uptrend[con])
        df.loc[con,'tod'] = C[i] > O[i] and (C[i] > O[y] and O[y] >= O[i]) and (C[i] >= C[y] and C[y] > O[i]) and O[x] > C[x] and (C[x] > O[i] and df.uptrend[con])
        df.loc[con,'es']  = C[i] > O[i] and abs(O[y] - C[y]) > 0 and C[y] > C[i] and O[y] > C[i] and O[x] > C[x] and (C[x] < 0.5*(C[y] + O[i]) and df.uptrend[con])

    def isabove(p, m):
        val_min = ta.MIN(p, m)
        val_max = ta.MAX(p, m)
        
        diff = (p - val_min) / (val_max - val_min)
        ma = ta.SMA(diff, m) * 2
        return (diff - ma) > 0.00
        
    df['above'] = isabove(V, lb)
    df['long_1day'] = 0
    df['short_1day'] = 0
    df['long_2day'] = 0
    df['short_2day'] = 0
    df['long_3day'] = 0
    df['short_3day'] = 0

    for i in range(0 ,df.index.stop):
        df.loc[i,'long_1day']  = df.factor[i] > uthres  and (df.wm[i] == True or df.cwm[i]  == True  or df.owm[i] == True or df.lwc[i]  == True  or df.dd[i]    == True  or df.wpu[i] == True  or df.bpu[i] == True )
        df.loc[i,'short_1day'] = df.factor[i] < lthres  and (df.bm[i] == True or df.cbm[i]  == True  or df.lbc[i] == True or df.obm[i]  == True  or df.gd[i]    == True  or df.bss[i] == True  or df.wss[i] == True ) 
        df.loc[i,'long_2day']  = df.factor[i] > uthres  and (df.hp[i] == True or df.bulle[i]== True  or df.pl[i]  == True or df.bullh[i]== True  or df.bullk[i] == True) 
        df.loc[i,'short_2day'] = df.factor[i] < lthres  and (df.dh[i] == True or df.beare[i]== True  or df.dcc[i] == True or df.bearh[i]== True  or df.beark[i] == True) 
        df.loc[i,'long_3day']  = df.factor[i] > uthres  and (df.tws[i]== True or df.tiu[i]  == True  or df.tou[i] == True or df.ms[i]   == True) 
        df.loc[i,'short_3day'] = df.factor[i] < lthres  and (df.tbc[i]== True or df.tid[i]  == True  or df.tod[i] == True or df.es[i]   == True)
  
    df['state'] = 0
        
    for i in range(1 ,df.index.stop):
        y = i -1
        if(df.long_1day[i] == True or df.long_2day[i] == True or df.long_3day[i] == True) and df.above[i] == True:
            df.loc[i,'state'] = 1
        elif(df.short_1day[i] == True or df.short_2day[i] == True or df.short_3day[i] == True) and df.above[i] == True :
            df.loc[i,'state'] = -1
        else:
            df.loc[i,'state'] = df.loc[y,'state']
       
    df['buy']   = False
    df['sell']  = False

    for i in range(1,df.index.stop):
        y = i -1


        if df.loc[i,'state'] > df.loc[y,'state']:
            df.loc[i,'buy'] = True #BUY

        elif df.loc[i,'state'] < df.loc[y,'state']:
            df.loc[i,'sell']  = True #SELL

    return df[['timeframe', 'close', 'buy' , 'sell']]

def send_update(chat_id, msg):
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={msg}"
    requests.get(url)

send_update(chat_id,'(NANO BOT) بسم الله الرحمن الرحيم الحمد لله رب العالمين تم تشغيل')

def check_buy_sell_signals(df):
    print("checking for buys and sell")
    print(df.tail(5))

    lest_row_index = len(df.index) - 1
    price = df.loc[lest_row_index,'close']

    if df.loc[lest_row_index,'buy'] == True:
        print('changed to uptrend, BUY')
        send_update(chat_id,f'باذن الله تم الشراء على سعر ال : {price}')
        order = exchange.create_market_buy_order('ETH/USDT',0.05)
        print(order)

    if df.loc[lest_row_index,'sell'] == True:
        print('changed to downtrend, SELL')
        send_update(chat_id, f"باذن الله تم البيع على سعر ال : {price}")
        order = exchange.create_market_sell_order('ETH/USDT',0.05)
        print(order)

def run_bar():
    print(f"Fetching new bars for {datetime.now().isoformat()}")
    bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='5m', limit=100)
    df = pd.DataFrame(bars[:-1], columns=['timeframe','open','high','low','close','volume'])
    df['timeframe'] = pd.to_datetime(df['timeframe'], unit='ms')
    candel = str(df)
    check_buy_sell_signals(candel)
# schedule.every(5).seconds.do(run_bar)
schedule.every(5).minutes.at(":05").do(run_bar)

while True:
    schedule.run_pending()
    time.sleep(1)

