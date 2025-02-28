import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './App.css'

const queryClient = new QueryClient()

function App() {
  const [isDarkMode, setIsDarkMode] = useState(true)

  return (
    <QueryClientProvider client={queryClient}>
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
                <div className="aspect-video bg-gray-100 dark:bg-gray-700 rounded-lg">
                  {/* TradingView Chart will go here */}
                </div>
              </div>
            </div>

            {/* Trading Panel */}
            <div className="lg:col-span-4 space-y-6">
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h2 className="text-xl font-semibold mb-4">AI Trading Panel</h2>
                <div className="space-y-4">
                  <div className="p-4 bg-green-100 dark:bg-green-900 rounded-lg">
                    <h3 className="font-medium text-green-800 dark:text-green-100">AI Suggestion</h3>
                    <p className="text-sm text-green-700 dark:text-green-200 mt-1">
                      Analyzing market conditions...
                    </p>
                  </div>
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
    </QueryClientProvider>
  )
}

export default App 