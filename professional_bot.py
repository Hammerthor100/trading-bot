import requests
import time
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import os
import talib
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging

print("💎 ПРОФЕССИОНАЛЬНЫЙ ТРЕЙДИНГ БОТ С ВИЗУАЛИЗАЦИЕЙ ЗАГРУЖАЕТСЯ...")

# ⚠️ ЗАМЕНИТЕ НА ВАШИ ДАННЫЕ!
TELEGRAM_TOKEN = "8537987175:AAHyuwgO_SJdrzL5pyjc11EfFjfHKrOC5-0"
CHAT_ID = "5819638872"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedTradingBot:
    def __init__(self):
        self.symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT']
        self.signals_history = []
        self.analysis_count = 0
        self.timeframes = {
            '1h': '1 час',
            '4h': '4 часа', 
            '1d': '1 день'
        }
        
    def create_main_keyboard(self):
        """Создаем профессиональное меню"""
        keyboard = [
            ["📊 Анализ рынка", "🎯 Мои сигналы"],
            ["📈 1H Анализ", "⏰ 4H Анализ", "📅 1D Анализ"],
            ["🔍 Анализ BTC", "💰 Анализ ETH", "🚀 Топ монеты"],
            ["⚙️ Настройки", "❓ Помощь"]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите действие...")

    def get_historical_data(self, symbol, interval='1h', limit=100):
        """Получаем исторические данные для анализа"""
        try:
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            response = requests.get(url)
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Конвертируем в числовые типы
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
                
            df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
            
            return df
        except Exception as e:
            logger.error(f"Ошибка получения данных {symbol}: {e}")
            return None

    def calculate_technical_indicators(self, df):
        """Рассчитываем все технические индикаторы"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        indicators = {}
        
        try:
            # Трендовые индикаторы
            indicators['sma_20'] = talib.SMA(close, timeperiod=20)
            indicators['sma_50'] = talib.SMA(close, timeperiod=50)
            indicators['ema_12'] = talib.EMA(close, timeperiod=12)
            indicators['ema_26'] = talib.EMA(close, timeperiod=26)
            indicators['ema_50'] = talib.EMA(close, timeperiod=50)
            
            # MACD
            indicators['macd'], indicators['macd_signal'], indicators['macd_hist'] = talib.MACD(close)
            
            # RSI
            indicators['rsi'] = talib.RSI(close, timeperiod=14)
            indicators['rsi_6'] = talib.RSI(close, timeperiod=6)  # Быстрый RSI
            
            # Stochastic
            indicators['stoch_k'], indicators['stoch_d'] = talib.STOCH(high, low, close)
            indicators['stoch_rsi'] = talib.STOCHRSI(close)
            
            # Bollinger Bands
            indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = talib.BBANDS(close)
            
            # Volume indicators
            indicators['ad'] = talib.AD(high, low, close, volume)
            indicators['obv'] = talib.OBV(close, volume)
            indicators['adx'] = talib.ADX(high, low, close)
            
            # Волатильность
            indicators['atr'] = talib.ATR(high, low, close)
            
            # Моментум
            indicators['momentum'] = talib.MOM(close, timeperiod=10)
            indicators['cci'] = talib.CCI(high, low, close)
            indicators['willr'] = talib.WILLR(high, low, close)
            
            # Parabolic SAR
            indicators['sar'] = talib.SAR(high, low)
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов: {e}")
            
        return indicators

    def generate_trading_signals(self, df, indicators):
        """Генерируем торговые сигналы на основе множества стратегий"""
        signals = []
        confidence_scores = []
        reasons = []
        
        current_price = df['close'].iloc[-1]
        current_rsi = indicators['rsi'][-1] if indicators['rsi'] is not None and len(indicators['rsi']) > 0 else 50
        
        # Стратегия 1: RSI + Перекупленность/перепроданность
        if current_rsi < 25:
            signals.append('BUY')
            confidence_scores.append(85)
            reasons.append(f"🎯 RSI {current_rsi:.1f} - СИЛЬНАЯ ПЕРЕПРОДАННОСТЬ")
        elif current_rsi > 75:
            signals.append('SELL')
            confidence_scores.append(85)
            reasons.append(f"🎯 RSI {current_rsi:.1f} - СИЛЬНАЯ ПЕРЕКУПЛЕННОСТЬ")
        elif current_rsi < 30:
            signals.append('BUY')
            confidence_scores.append(70)
            reasons.append(f"📊 RSI {current_rsi:.1f} - перепроданность")
        elif current_rsi > 70:
            signals.append('SELL')
            confidence_scores.append(70)
            reasons.append(f"📊 RSI {current_rsi:.1f} - перекупленность")
        
        # Стратегия 2: MACD
        if indicators['macd'] is not None and len(indicators['macd']) > 1:
            macd_current = indicators['macd'][-1]
            macd_prev = indicators['macd'][-2]
            signal_current = indicators['macd_signal'][-1]
            macd_hist = indicators['macd_hist'][-1]
            
            if macd_current > signal_current and macd_prev <= signal_current and macd_hist > 0:
                signals.append('BUY')
                confidence_scores.append(80)
                reasons.append("📈 MACD пересек сигнальную линию СНИЗУ ВВЕРХ")
            elif macd_current < signal_current and macd_prev >= signal_current and macd_hist < 0:
                signals.append('SELL')
                confidence_scores.append(80)
                reasons.append("📈 MACD пересек сигнальную линию СВЕРХУ ВНИЗ")
        
        # Стратегия 3: Скользящие средние
        if indicators['sma_20'] is not None and indicators['sma_50'] is not None:
            sma_20 = indicators['sma_20'][-1]
            sma_50 = indicators['sma_50'][-1]
            ema_12 = indicators['ema_12'][-1]
            ema_26 = indicators['ema_26'][-1]
            
            # Золотое/мертвое пересечение
            if sma_20 > sma_50 and indicators['sma_20'][-2] <= indicators['sma_50'][-2]:
                signals.append('BUY')
                confidence_scores.append(85)
                reasons.append("💰 ЗОЛОТОЕ ПЕРЕСЕЧЕНИЕ SMA20/SMA50")
            elif sma_20 < sma_50 and indicators['sma_20'][-2] >= indicators['sma_50'][-2]:
                signals.append('SELL')
                confidence_scores.append(85)
                reasons.append("💰 МЕРТВОЕ ПЕРЕСЕЧЕНИЕ SMA20/SMA50")
            
            # EMA пересечение
            if ema_12 > ema_26 and indicators['ema_12'][-2] <= indicators['ema_26'][-2]:
                signals.append('BUY')
                confidence_scores.append(80)
                reasons.append("📊 Бычье пересечение EMA12/EMA26")
        
        # Стратегия 4: Боллинджер Бэнды
        if indicators['bb_upper'] is not None and indicators['bb_lower'] is not None:
            bb_upper = indicators['bb_upper'][-1]
            bb_lower = indicators['bb_lower'][-1]
            bb_middle = indicators['bb_middle'][-1]
            
            if current_price <= bb_lower * 1.02:  # 2% от нижней полосы
                signals.append('BUY')
                confidence_scores.append(75)
                reasons.append("🎯 Цена КАСАЕТСЯ нижней полосы Боллинджера")
            elif current_price >= bb_upper * 0.98:  # 2% от верхней полосы
                signals.append('SELL')
                confidence_scores.append(75)
                reasons.append("🎯 Цена КАСАЕТСЯ верхней полосы Боллинджера")
            elif current_price > bb_middle and indicators['close'].iloc[-2] <= bb_middle:
                signals.append('BUY')
                confidence_scores.append(65)
                reasons.append("📈 Цена ПРОБИЛА среднюю линию Боллинджера ВВЕРХ")
        
        # Стратегия 5: Stochastic
        if indicators['stoch_k'] is not None and indicators['stoch_d'] is not None:
            stoch_k = indicators['stoch_k'][-1]
            stoch_d = indicators['stoch_d'][-1]
            
            if stoch_k < 20 and stoch_d < 20 and stoch_k > stoch_d:
                signals.append('BUY')
                confidence_scores.append(70)
                reasons.append("🔮 Stochastic в зоне ПЕРЕПРОДАННОСТИ с БЫЧЬИМ пересечением")
            elif stoch_k > 80 and stoch_d > 80 and stoch_k < stoch_d:
                signals.append('SELL')
                confidence_scores.append(70)
                reasons.append("🔮 Stochastic в зоне ПЕРЕКУПЛЕННОСТИ с МЕДВЕЖЬИМ пересечением")
        
        # Стратегия 6: Volume анализ
        if indicators['obv'] is not None and len(indicators['obv']) > 1:
            obv_current = indicators['obv'][-1]
            obv_prev = indicators['obv'][-2]
            volume_trend = obv_current > obv_prev
            
            if volume_trend and current_price > df['close'].iloc[-2]:
                signals.append('BUY')
                confidence_scores.append(65)
                reasons.append("💎 РОСТ ОБЪЕМА на ПОВЫШЕНИИ цены")
            elif volume_trend and current_price < df['close'].iloc[-2]:
                signals.append('SELL')
                confidence_scores.append(65)
                reasons.append("💎 РОСТ ОБЪЕМА на ПОНИЖЕНИИ цены")
        
        # Стратегия 7: ADX (сила тренда)
        if indicators['adx'] is not None:
            adx = indicators['adx'][-1]
            if adx > 25:
                reasons.append(f"🌀 Сильный тренд (ADX: {adx:.1f})")
        
        # Определяем итоговый сигнал
        if not signals:
            return 'HOLD', 0, ["Недостаточно сигналов для торговли"]
        
        buy_signals = signals.count('BUY')
        sell_signals = signals.count('SELL')
        
        if buy_signals > sell_signals:
            final_signal = 'BUY'
            confidence = np.mean([score for signal, score in zip(signals, confidence_scores) if signal == 'BUY'])
        elif sell_signals > buy_signals:
            final_signal = 'SELL'
            confidence = np.mean([score for signal, score in zip(signals, confidence_scores) if signal == 'SELL'])
        else:
            final_signal = 'HOLD'
            confidence = 0
        
        return final_signal, min(95, confidence), reasons

    def create_advanced_chart(self, symbol, df, indicators, signal, confidence, reasons, timeframe='1h'):
        """Создаем продвинутый свечной график с анализом"""
        try:
            if not os.path.exists('advanced_charts'):
                os.makedirs('advanced_charts')
            
            plt.style.use('dark_background')
            fig = plt.figure(figsize=(16, 14))
            gs = fig.add_gridspec(4, 1, height_ratios=[3, 1, 1, 1])
            
            ax1 = fig.add_subplot(gs[0])  # Цена и свечи
            ax2 = fig.add_subplot(gs[1])  # RSI
            ax3 = fig.add_subplot(gs[2])  # MACD
            ax4 = fig.add_subplot(gs[3])  # Volume
            
            # Берем последние 50 свечей для лучшей визуализации
            plot_data = df.tail(50)
            dates = plot_data['timestamp']
            
            # 1. СВЕЧНОЙ ГРАФИК С ИНДИКАТОРАМИ
            self.plot_candlestick(ax1, plot_data, indicators, signal, symbol, timeframe)
            
            # 2. RSI ИНДИКАТОР
            self.plot_rsi(ax2, plot_data, indicators)
            
            # 3. MACD ИНДИКАТОР
            self.plot_macd(ax3, plot_data, indicators)
            
            # 4. VOLUME ИНДИКАТОР
            self.plot_volume(ax4, plot_data)
            
            # ОБЩИЙ ЗАГОЛОВОК
            signal_color = '#00ff88' if signal == 'BUY' else '#ff4444' if signal == 'SELL' else '#ffff00'
            title_text = f'🎯 {symbol} | {timeframe.upper()} | СИГНАЛ: {signal} | УВЕРЕННОСТЬ: {confidence:.1f}%'
            fig.suptitle(title_text, fontsize=18, fontweight='bold', color=signal_color, y=0.95)
            
            # ИНФОРМАЦИОННАЯ ПАНЕЛЬ
            self.add_info_panel(fig, symbol, df, indicators, signal, confidence, reasons, timeframe)
            
            plt.tight_layout()
            plt.subplots_adjust(top=0.92, bottom=0.08)
            
            filename = f"advanced_charts/{symbol}_{timeframe}_{int(time.time())}.png"
            plt.savefig(filename, dpi=120, bbox_inches='tight', facecolor='#0c0c0c')
            plt.close()
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка создания графика: {e}")
            return None

    def plot_candlestick(self, ax, df, indicators, signal, symbol, timeframe):
        """Создаем свечной график с индикаторами"""
        # Свечной график
        for i, (idx, row) in enumerate(df.iterrows()):
            open_price = row['open']
            close_price = row['close']
            high_price = row['high']
            low_price = row['low']
            
            # Цвет свечи
            color = '#00ff88' if close_price >= open_price else '#ff4444'
            alpha = 0.8
            
            # Тело свечи
            body_bottom = min(open_price, close_price)
            body_top = max(open_price, close_price)
            body_height = body_top - body_bottom
            
            if body_height > 0:
                rect = Rectangle((i - 0.3, body_bottom), 0.6, body_height,
                               facecolor=color, alpha=alpha, edgecolor=color)
                ax.add_patch(rect)
            
            # Тени свечи
            ax.plot([i, i], [low_price, body_bottom], color=color, alpha=alpha, linewidth=1)
            ax.plot([i, i], [body_top, high_price], color=color, alpha=alpha, linewidth=1)
        
        # Добавляем скользящие средние
        if indicators['sma_20'] is not None:
            sma_20 = indicators['sma_20'][-50:]
            ax.plot(range(len(sma_20)), sma_20, color='orange', linewidth=2, label='SMA 20', alpha=0.8)
        
        if indicators['sma_50'] is not None:
            sma_50 = indicators['sma_50'][-50:]
            ax.plot(range(len(sma_50)), sma_50, color='red', linewidth=2, label='SMA 50', alpha=0.8)
        
        if indicators['ema_12'] is not None:
            ema_12 = indicators['ema_12'][-50:]
            ax.plot(range(len(ema_12)), ema_12, color='cyan', linewidth=1.5, label='EMA 12', alpha=0.7)
        
        # Боллинджер Бэнды
        if indicators['bb_upper'] is not None:
            bb_upper = indicators['bb_upper'][-50:]
            bb_lower = indicators['bb_lower'][-50:]
            ax.fill_between(range(len(bb_upper)), bb_upper, bb_lower, color='gray', alpha=0.2, label='Bollinger Bands')
        
        # Точки входа/выхода
        current_idx = len(df) - 1
        current_price = df['close'].iloc[-1]
        
        # Размечаем точку входа
        marker_color = '#00ff00' if signal == 'BUY' else '#ff0000' if signal == 'SELL' else '#ffff00'
        marker_shape = '^' if signal == 'BUY' else 'v' if signal == 'SELL' else 'o'
        
        ax.scatter(current_idx, current_price, color=marker_color, marker=marker_shape, 
                  s=200, zorder=5, edgecolors='white', linewidth=2)
        
        ax.set_ylabel('Цена (USDT)', color='white')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)

    def plot_rsi(self, ax, df, indicators):
        """График RSI"""
        if indicators['rsi'] is not None:
            rsi_data = indicators['rsi'][-50:]
            ax.plot(range(len(rsi_data)), rsi_data, color='purple', linewidth=2, label='RSI 14')
            ax.axhline(y=70, color='red', linestyle='--', alpha=0.7, label='Перекупленность')
            ax.axhline(y=30, color='green', linestyle='--', alpha=0.7, label='Перепроданность')
            ax.axhline(y=50, color='white', linestyle='-', alpha=0.3)
            ax.set_ylim(0, 100)
            ax.set_ylabel('RSI', color='white')
            ax.legend()
            ax.grid(True, alpha=0.3)

    def plot_macd(self, ax, df, indicators):
        """График MACD"""
        if indicators['macd'] is not None:
            macd_data = indicators['macd'][-50:]
            macd_signal = indicators['macd_signal'][-50:]
            macd_hist = indicators['macd_hist'][-50:]
            
            ax.plot(range(len(macd_data)), macd_data, color='blue', linewidth=2, label='MACD')
            ax.plot(range(len(macd_signal)), macd_signal, color='red', linewidth=2, label='Signal')
            
            # Гистограмма MACD
            colors = ['#00ff88' if x >= 0 else '#ff4444' for x in macd_hist]
            ax.bar(range(len(macd_hist)), macd_hist, color=colors, alpha=0.6, label='Histogram')
            
            ax.axhline(y=0, color='white', linestyle='-', alpha=0.5)
            ax.set_ylabel('MACD', color='white')
            ax.legend()
            ax.grid(True, alpha=0.3)

    def plot_volume(self, ax, df):
        """График объема"""
        volumes = df['volume'].values
        colors = ['#00ff88' if df['close'].iloc[i] >= df['open'].iloc[i] else '#ff4444' 
                 for i in range(len(df))]
        
        ax.bar(range(len(volumes)), volumes, color=colors, alpha=0.6)
        ax.set_ylabel('Volume', color='white')
        ax.grid(True, alpha=0.3)

    def add_info_panel(self, fig, symbol, df, indicators, signal, confidence, reasons, timeframe):
        """Добавляем информационную панель"""
        current_price = df['close'].iloc[-1]
        price_change = ((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
        volume = df['volume'].iloc[-1]
        
        info_text = f"""
💎 ТЕХНИЧЕСКИЙ АНАЛИЗ {symbol}

💰 Цена: ${current_price:.2f}
📈 Изменение: {price_change:+.2f}%
📊 Объем: {volume:,.0f}
🎯 Сигнал: {signal}
💪 Уверенность: {confidence:.1f}%
⏰ Таймфрейм: {timeframe.upper()}

📊 ИНДИКАТОРЫ:
RSI: {indicators['rsi'][-1] if indicators['rsi'] is not None else 'N/A':.1f}
MACD: {indicators['macd'][-1] if indicators['macd'] is not None else 'N/A':.4f}
Stoch K: {indicators['stoch_k'][-1] if indicators['stoch_k'] is not None else 'N/A':.1f}

🎯 ОСНОВАНИЯ:
""" + "\n".join([f"• {r}" for r in reasons[:4]]) + f"""

⏰ Анализ: {datetime.datetime.now().strftime('%H:%M:%S')}
"""

        fig.text(0.02, 0.02, info_text, fontsize=10, color='lightblue',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#1a1a2e", alpha=0.9),
                verticalalignment='bottom')

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        welcome_text = """
💎 *ПРОФЕССИОНАЛЬНЫЙ ТРЕЙДИНГ БОТ С ВИЗУАЛИЗАЦИЕЙ* 💎

*Новые возможности:*
• 📊 Свечные графики вместо линейных
• ⏰ Разные таймфреймы (1H, 4H, 1D)
• 🎯 Больше индикаторов на графиках
• 📈 Точки входа/выхода на графике
• 🎨 Цветовая схема сигналов

*Выберите таймфрейм для анализа:* 👇
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=self.create_main_keyboard(),
            parse_mode='Markdown'
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик сообщений"""
        text = update.message.text
        
        if text == "📊 Анализ рынка":
            await self.full_market_analysis(update, '1h')
        elif text == "🎯 Мои сигналы":
            await self.show_my_signals(update)
        elif text == "📈 1H Анализ":
            await self.full_market_analysis(update, '1h')
        elif text == "⏰ 4H Анализ":
            await self.full_market_analysis(update, '4h')
        elif text == "📅 1D Анализ":
            await self.full_market_analysis(update, '1d')
        elif text == "🔍 Анализ BTC":
            await self.analyze_btc(update, '1h')
        elif text == "💰 Анализ ETH":
            await self.analyze_eth(update, '1h')
        elif text == "🚀 Топ монеты":
            await self.top_coins_analysis(update)
        elif text == "⚙️ Настройки":
            await self.show_settings(update)
        elif text == "❓ Помощь":
            await self.show_help(update)

    async def full_market_analysis(self, update: Update, timeframe='1h'):
        """Полный анализ рынка с выбранным таймфреймом"""
        message = await update.message.reply_text(f"🔮 *Запускаю {timeframe.upper()} анализ рынка...*", parse_mode='Markdown')
        
        strong_signals = []
        
        for symbol in self.symbols[:4]:  # Анализируем первые 4 пары для скорости
            try:
                # Получаем исторические данные
                df = self.get_historical_data(symbol, interval=timeframe, limit=100)
                if df is None or len(df) < 50:
                    continue
                
                # Рассчитываем индикаторы
                indicators = self.calculate_technical_indicators(df)
                
                # Генерируем сигналы
                signal, confidence, reasons = self.generate_trading_signals(df, indicators)
                
                if signal != 'HOLD' and confidence >= 60:
                    # Создаем профессиональный график
                    chart_path = self.create_advanced_chart(symbol, df, indicators, signal, confidence, reasons, timeframe)
                    
                    signal_data = {
                        'symbol': symbol,
                        'signal': signal,
                        'confidence': confidence,
                        'price': df['close'].iloc[-1],
                        'timeframe': timeframe,
                        'reasons': reasons,
                        'timestamp': datetime.datetime.now().isoformat(),
                        'chart_path': chart_path
                    }
                    
                    strong_signals.append(signal_data)
                    
                    # Отправляем сигнал с графиком
                    if chart_path and os.path.exists(chart_path):
                        signal_text = self.format_signal_message(signal_data)
                        
                        with open(chart_path, 'rb') as photo:
                            await update.message.reply_photo(
                                photo=photo,
                                caption=signal_text,
                                parse_mode='Markdown'
                            )
                    
                    time.sleep(1)  # Пауза между отправками
                    
            except Exception as e:
                logger.error(f"Ошибка анализа {symbol}: {e}")
                continue
        
        # Сохраняем в историю
        self.signals_history.extend(strong_signals)
        self.analysis_count += 1
        
        summary = f"✅ *{timeframe.upper()} анализ завершен!* Найдено *{len(strong_signals)}* сильных сигналов"
        await message.edit_text(summary, parse_mode='Markdown')

    def format_signal_message(self, signal_data):
        """Форматируем сообщение о сигнале"""
        emoji = "🟢" if signal_data['signal'] == 'BUY' else "🔴"
        
        message = f"""
{emoji} *ПРОФЕССИОНАЛЬНЫЙ СИГНАЛ*

*Монета:* {signal_data['symbol']}
*Таймфрейм:* {signal_data['timeframe'].upper()}
*Сигнал:* {signal_data['signal']}
*Уверенность:* {signal_data['confidence']:.1f}%
*Цена:* ${signal_data['price']:.2f}

*📊 Технические основания:*
""" + "\n".join([f"• {r}" for r in signal_data['reasons'][:3]]) + """

*⏰ Время анализа:* """ + datetime.datetime.now().strftime('%H:%M:%S') + """

💡 *Рекомендация:* """ + ("РАССМОТРЕТЬ ПОКУПКУ" if signal_data['signal'] == 'BUY' else "РАССМОТРЕТЬ ПРОДАЖУ")

        return message

    async def show_my_signals(self, update: Update):
        """Показываем историю сигналов"""
        if not self.signals_history:
            await update.message.reply_text("📭 *История сигналов пуста*\nСначала выполните анализ рынка")
            return
        
        # Группируем сигналы по типам
        buy_signals = [s for s in self.signals_history if s['signal'] == 'BUY']
        sell_signals = [s for s in self.signals_history if s['signal'] == 'SELL']
        
        message = f"""
📈 *ИСТОРИЯ СИГНАЛОВ*

*Всего анализов:* {self.analysis_count}
*Активные сигналы:* {len(self.signals_history)}

🟢 *Сигналы ПОКУПКИ:* {len(buy_signals)}
🔴 *Сигналы ПРОДАЖИ:* {len(sell_signals)}

*Последние 3 сигнала:*
"""
        
        for signal in self.signals_history[-3:]:
            time_ago = datetime.datetime.now() - datetime.datetime.fromisoformat(signal['timestamp'])
            minutes_ago = int(time_ago.total_seconds() / 60)
            
            message += f"\n• {signal['symbol']} ({signal['timeframe']}): {signal['signal']} ({signal['confidence']:.1f}%) - {minutes_ago} мин. назад"
        
        await update.message.reply_text(message, parse_mode='Markdown')

    async def analyze_btc(self, update: Update, timeframe='1h'):
        """Глубокий анализ BTC"""
        await self.analyze_single_coin(update, 'BTCUSDT', 'BITCOIN (BTC)', timeframe)

    async def analyze_eth(self, update: Update, timeframe='1h'):
        """Глубокий анализ ETH"""
        await self.analyze_single_coin(update, 'ETHUSDT', 'ETHEREUM (ETH)', timeframe)

    async def analyze_single_coin(self, update: Update, symbol, name, timeframe):
        """Анализ одной монеты"""
        message = await update.message.reply_text(f"🔍 *Запускаю {timeframe.upper()} анализ {name}...*", parse_mode='Markdown')
        
        try:
            df = self.get_historical_data(symbol, interval=timeframe, limit=100)
            if df is None or len(df) < 50:
                await message.edit_text("❌ *Ошибка получения данных*")
                return
            
            indicators = self.calculate_technical_indicators(df)
            signal, confidence, reasons = self.generate_trading_signals(df, indicators)
            
            # Создаем детальный график
            chart_path = self.create_advanced_chart(symbol, df, indicators, signal, confidence, reasons, timeframe)
            
            # Формируем детальный отчет
            report = self.create_detailed_report(symbol, df, indicators, signal, confidence, reasons, timeframe)
            
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, 'rb') as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption=report,
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text(report, parse_mode='Markdown')
                
            await message.delete()
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            await message.edit_text("❌ *Ошибка при анализе*")

    def create_detailed_report(self, symbol, df, indicators, signal, confidence, reasons, timeframe):
        """Создаем детальный отчет"""
        current_price = df['close'].iloc[-1]
        price_change = ((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
        
        report = f"""
💎 *ДЕТАЛЬНЫЙ АНАЛИЗ {symbol}*

*Таймфрейм:* {timeframe.upper()}
*Текущая цена:* ${current_price:.2f}
*Изменение за период:* {price_change:+.2f}%
*Торговый сигнал:* {signal}
*Уверенность системы:* {confidence:.1f}%

*📊 ТЕХНИЧЕСКИЕ ПОКАЗАТЕЛИ:*
• RSI: {indicators['rsi'][-1] if indicators['rsi'] is not None else 'N/A':.1f}
• MACD: {indicators['macd'][-1] if indicators['macd'] is not None else 'N/A':.4f}
• Stochastic K: {indicators['stoch_k'][-1] if indicators['stoch_k'] is not None else 'N/A':.1f}
• ATR (волатильность): {indicators['atr'][-1] if indicators['atr'] is not None else 'N/A':.4f}
• ADX (сила тренда): {indicators['adx'][-1] if indicators['adx'] is not None else 'N/A':.1f}

*🎯 ОСНОВАНИЯ ДЛЯ СИГНАЛА:*
""" + "\n".join([f"• {r}" for r in reasons[:5]]) + """

*⏰ Время анализа:* """ + datetime.datetime.now().strftime('%H:%M:%S') + """

⚠️ *Дисклеймер:* Торгуйте ответственно, используйте стоп-лоссы
        """
        
        return report

    async def top_coins_analysis(self, update: Update):
        """Анализ топовых монет"""
        await update.message.reply_text("🚀 *Анализирую самые перспективные монеты...*", parse_mode='Markdown')
        
        # Анализируем BTC, ETH, BNB
        top_coins = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        results = []
        
        for symbol in top_coins:
            df = self.get_historical_data(symbol, interval='4h', limit=50)
            if df is not None:
                indicators = self.calculate_technical_indicators(df)
                signal, confidence, reasons = self.generate_trading_signals(df, indicators)
                
                emoji = "🟢" if signal == 'BUY' else "🔴" if signal == 'SELL' else "🟡"
                results.append(f"{emoji} *{symbol}*: {signal} ({confidence:.1f}%) - ${df['close'].iloc[-1]:.2f}")
        
        if results:
            result_text = "🏆 *ТОП МОНЕТЫ ДЛЯ ТОРГОВЛИ:*\n\n" + "\n".join(results)
        else:
            result_text = "❌ *Не удалось получить данные*"
        
        await update.message.reply_text(result_text, parse_mode='Markdown')

    async def show_settings(self, update: Update):
        """Настройки бота"""
        settings_text = f"""
⚙️ *НАСТРОЙКИ БОТА*

*Текущие настройки:*
• Анализируемые пары: {len(self.symbols)}
• Всего анализов: {self.analysis_count}
• Сигналов в истории: {len(self.signals_history)}
• Доступные таймфреймы: 1H, 4H, 1D

*Доступные пары:* {', '.join(self.symbols)}

*Для изменения настроек обратитесь к разработчику*
        """
        
        await update.message.reply_text(settings_text, parse_mode='Markdown')

    async def show_help(self, update: Update):
        """Помощь"""
        help_text = """
❓ *ПОМОЩЬ ПО ПРОФЕССИОНАЛЬНОМУ БОТУ*

*🎯 Основные функции:*
• *📊 Анализ рынка* - Полный технический анализ (1H)
• *📈 1H/⏰ 4H/📅 1D Анализ* - Анализ на разных таймфреймах
• *🎯 Мои сигналы* - История и статистика
• *🔍 Анализ BTC/ETH* - Детальный анализ лидеров

*📊 НОВАЯ ВИЗУАЛИЗАЦИЯ:*
• Свечные графики вместо линейных
• 4 панели: Цена, RSI, MACD, Volume
• Точки входа/выхода на графике
• Цветовая схема сигналов
• Разные таймфреймы

*💡 Сигналы:*
🟢 BUY - Уверенность > 60%
🔴 SELL - Уверенность > 60% 
🟡 HOLD - Недостаточно сигналов

⚠️ *ВАЖНО:* Это профессиональный инструмент для анализа. Торгуйте ответственно!
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

# Создаем и запускаем бота
bot = AdvancedTradingBot()

def main():
    """Запускаем профессионального бота"""
    print("💎 Запускаю профессионального торгового бота с визуализацией...")
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("✅ Профессиональный бот запущен!")
    print("📱 Перейдите в Telegram и напишите /start")
    
    # Запускаем бота
    application.run_polling()

if __name__ == "__main__":
    main()
