import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MarketDataProvider } from './contexts/MarketDataContext'
import { MarketDataDisplay } from './components/MarketDataDisplay'
import './App.css'

const queryClient = new QueryClient()

// Default symbols to track
const DEFAULT_SYMBOLS = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META']

function App() {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null)

  const handleSymbolClick = (symbol: string) => {
    setSelectedSymbol(symbol)
    // TODO: Open detailed view/trading panel for the selected symbol
  }

  return (
    <QueryClientProvider client={queryClient}>
      <MarketDataProvider>
        <div className={`min-h-screen ${isDarkMode ? 'dark bg-gray-900 text-white' : 'bg-white text-gray-900'}`}>
          <header className="border-b border-gray-200 dark:border-gray-700">
            <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
              <div className="flex items-center space-x-4">
                <h1 className="text-2xl font-bold">AI Trader Pro</h1>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => setIsDarkMode(!isDarkMode)}
                  className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
                >
                  {isDarkMode ? '🌞' : '🌙'}
                </button>
              </div>
            </nav>
          </header>

          <main className="container mx-auto px-4 py-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Market Overview */}
              <div className="lg:col-span-8 space-y-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Market Overview</h2>
                  <MarketDataDisplay
                    symbols={DEFAULT_SYMBOLS}
                    onSymbolClick={handleSymbolClick}
                  />
                </div>
              </div>

              {/* Trading Panel */}
              <div className="lg:col-span-4 space-y-6">
                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">AI Trading Panel</h2>
                  <div className="space-y-4">
                    {selectedSymbol ? (
                      <div className="p-4 bg-blue-100 dark:bg-blue-900 rounded-lg">
                        <h3 className="font-medium text-blue-800 dark:text-blue-100">
                          Analyzing {selectedSymbol}
                        </h3>
                        <p className="text-sm text-blue-700 dark:text-blue-200 mt-1">
                          AI is analyzing market conditions...
                        </p>
                      </div>
                    ) : (
                      <div className="p-4 bg-gray-100 dark:bg-gray-700 rounded-lg">
                        <p className="text-sm">
                          Select a symbol from the market overview to start trading
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                  <h2 className="text-xl font-semibold mb-4">Portfolio Overview</h2>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Total Value</span>
                      <span className="font-semibold">$0.00</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Daily P/L</span>
                      <span className="text-green-500">+$0.00 (0.00%)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </main>
        </div>
      </MarketDataProvider>
    </QueryClientProvider>
  )
}

export default App
