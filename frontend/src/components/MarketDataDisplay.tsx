import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, IChartApi } from 'lightweight-charts';

interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  timestamp: string;
  high: number;
  low: number;
  open: number;
  trading_signal?: 'BUY' | 'SELL' | 'HOLD';
  signal_confidence?: number;
  indicators?: {
    rsi: number;
    macd: number;
    macd_signal: number;
    bb_upper: number;
    bb_lower: number;
    bb_middle: number;
  };
}

interface MarketDataDisplayProps {
  data: MarketData | null;
}

const MarketDataDisplay: React.FC<MarketDataDisplayProps> = ({ data }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Initialize chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#D9D9D9',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
    });

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    // Create volume series
    const volumeSeries = chart.addHistogramSeries({
      color: '#385263',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    chartRef.current = chart;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
      }
    };
  }, []);

  // Update chart data
  useEffect(() => {
    if (!data || !chartRef.current) return;

    const timestamp = new Date(data.timestamp).getTime() / 1000;
    const candleData = {
      time: timestamp,
      open: data.open,
      high: data.high,
      low: data.low,
      close: data.price,
    };

    const volumeData = {
      time: timestamp,
      value: data.volume,
      color: data.price >= data.open ? '#26a69a50' : '#ef535050',
    };

    const candlestickSeries = chartRef.current.series()[0];
    const volumeSeries = chartRef.current.series()[1];

    candlestickSeries.update(candleData);
    volumeSeries.update(volumeData);
  }, [data]);

  return (
    <div className="space-y-4">
      {/* Market Data Header */}
      {data && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Price</h3>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              ${data.price.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Volume</h3>
            <p className="text-lg font-semibold text-gray-900 dark:text-white">
              {data.volume.toLocaleString()}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Signal</h3>
            <div className="flex items-center space-x-2">
              <p className={`text-lg font-semibold ${
                data.trading_signal === 'BUY' ? 'text-green-600' :
                data.trading_signal === 'SELL' ? 'text-red-600' :
                'text-gray-600'
              }`}>
                {data.trading_signal || 'HOLD'}
              </p>
              {data.signal_confidence && (
                <span className="text-sm text-gray-500">
                  ({(data.signal_confidence * 100).toFixed(1)}%)
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Chart */}
      <div ref={chartContainerRef} className="h-[400px]" />

      {/* Technical Indicators */}
      {data?.indicators && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">RSI</h3>
            <p className={`text-lg font-semibold ${
              data.indicators.rsi > 70 ? 'text-red-600' :
              data.indicators.rsi < 30 ? 'text-green-600' :
              'text-gray-900 dark:text-white'
            }`}>
              {data.indicators.rsi.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">MACD</h3>
            <p className={`text-lg font-semibold ${
              data.indicators.macd > data.indicators.macd_signal ? 'text-green-600' : 'text-red-600'
            }`}>
              {data.indicators.macd.toFixed(2)}
            </p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Bollinger Bands</h3>
            <div className="space-y-1">
              <p className="text-sm text-gray-500">Upper: ${data.indicators.bb_upper.toFixed(2)}</p>
              <p className="text-sm text-gray-500">Middle: ${data.indicators.bb_middle.toFixed(2)}</p>
              <p className="text-sm text-gray-500">Lower: ${data.indicators.bb_lower.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketDataDisplay; 