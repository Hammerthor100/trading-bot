import requests
import matplotlib.pyplot as plt
import datetime
import time
import os

class SimpleTradingBot:
    def __init__(self):
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
    def get_price(self, symbol):
        try:
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
            response = requests.get(url)
            data = response.json()
            return {
                'symbol': symbol,
                'price': float(data['lastPrice']),
                'change': float(data['priceChangePercent']),
                'high': float(data['highPrice']),
                'low': float(data['lowPrice'])
            }
        except:
            return None
    
    def analyze(self, price_data):
        if not price_data:
            return "HOLD", 0, ["Ошибка получения данных"]
            
        signals = []
        reasons = []
        
        # Анализ изменения цены
        if price_data['change'] > 3:
            signals.append('BUY')
            reasons.append(f"Цена выросла на {price_data['change']:.2f}%")
        elif price_data['change'] < -3:
            signals.append('SELL') 
            reasons.append(f"Цена упала на {abs(price_data['change']):.2f}%")
            
        # Анализ волатильности
        volatility = (price_data['high'] - price_data['low']) / price_data['price'] * 100
        if volatility > 5:
            reasons.append(f"Высокая волатильность: {volatility:.1f}%")
            
        # Определяем сигнал
        buy_count = signals.count('BUY')
        sell_count = signals.count('SELL')
        
        if buy_count > sell_count:
            return 'BUY', min(80, buy_count * 40), reasons
        elif sell_count > buy_count:
            return 'SELL', min(80, sell_count * 40), reasons
        else:
            return 'HOLD', 0, reasons or ["Нет четких сигналов"]
    
    def create_chart(self, symbol, price_data, signal, confidence, reasons):
        if not os.path.exists('charts'):
            os.makedirs('charts')
            
        plt.figure(figsize=(10, 6))
        plt.style.use('dark_background')
        
        # Создаем простой график
        prices = [price_data['low'], price_data['price'], price_data['high']]
        labels = ['Min', 'Current', 'Max']
        colors = ['red', 'yellow', 'green']
        
        plt.bar(labels, prices, color=colors, alpha=0.7)
        plt.title(f'Торговый сигнал: {symbol} - {signal}', fontsize=16, fontweight='bold', color='white')
        plt.ylabel('Цена (USD)', fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # Добавляем информацию
        info_text = f"Цена: ${price_data['price']:.2f}\n"
        info_text += f"Изменение: {price_data['change']:.2f}%\n"
        info_text += f"Уверенность: {confidence}%\n"
        info_text += "Причины:\n" + "\n".join([f"• {r}" for r in reasons])
        
        plt.figtext(0.02, 0.02, info_text, fontsize=10, color='lightblue',
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="darkblue", alpha=0.7))
        
        filename = f"charts/signal_{symbol}_{int(time.time())}.png"
        plt.savefig(filename, dpi=100, bbox_inches='tight')
        plt.close()
        
        return filename
    
    def run(self):
        print("🤖 Простой торговый бот запущен!")
        print("📊 Анализирую рынок...\n")
        
        for symbol in self.symbols:
            print(f"🔍 Анализирую {symbol}...")
            
            # Получаем данные
            price_data = self.get_price(symbol)
            
            if price_data:
                # Анализируем
                signal, confidence, reasons = self.analyze(price_data)
                
                if signal != 'HOLD':
                    print(f"🎯 СИГНАЛ: {signal} {symbol}!")
                    print(f"💪 Уверенность: {confidence}%")
                    print(f"💰 Цена: ${price_data['price']:.2f}")
                    print("📋 Причины:")
                    for reason in reasons:
                        print(f"   • {reason}")
                    
                    # Создаем график
                    chart_path = self.create_chart(symbol, price_data, signal, confidence, reasons)
                    print(f"📊 График сохранен: {chart_path}")
                    
                    # Рассчитываем цели
                    if signal == 'BUY':
                        tp = price_data['price'] * 1.03
                        sl = price_data['price'] * 0.98
                    else:
                        tp = price_data['price'] * 0.97
                        sl = price_data['price'] * 1.02
                        
                    print(f"🎯 Take Profit: ${tp:.2f}")
                    print(f"🛡️ Stop Loss: ${sl:.2f}")
                else:
                    print(f"➖ Нет сигнала для {symbol}")
                    
            print("-" * 50)
            time.sleep(1)  # Пауза между запросами

# Запускаем бота
if __name__ == "__main__":
    bot = SimpleTradingBot()
    bot.run()
